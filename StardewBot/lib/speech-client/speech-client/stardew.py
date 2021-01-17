import time
import traceback
import weakref
import functools
import queue
import sys
import asyncio
import threading
import uuid
import json
from dragonfly import *
from srabuilder import rules

from srabuilder.actions import directinput
import constants, server

active_objective = None
pending_objective = None
streams = weakref.WeakValueDictionary()


class GameState:
    def __init__(self):
        self.last_warp = None



class ObjectiveFailedError(BaseException):
    pass


class Objective:
    async def run(self):
        raise NotImplementedError

    async def wrap_run(self):
        self.full_task = asyncio.create_task(self.run_and_cancel())
        await self.full_task

    async def run_and_cancel(self):
        name = self.__class__.__name__
        server.log(f"Starting objective {name}")
        self.run_task = asyncio.create_task(self.run())
        try:
            await self.run_task
        except (Exception, ObjectiveFailedError) as e:
            err = e
            tb = traceback.format_exc()
            server.log(f"Objective {name} errored: \n{tb}")
        except asyncio.CancelledError as e:
            err = e
            server.log(f"Canceling objective {name}")
        else:
            err = None
            server.log(f"Successfully completed objective {name}")
        await self.cleanup(err)

    async def cleanup(self, exception):
        pass

    def fail(self, msg=None):
        if msg is None:
            msg = "Objective {self.__class__.__name__} failed"
        raise ObjectiveFailedError(msg)


class HoldKeyObjective(Objective):
    def __init__(self, keys):
        self.keys = keys

    async def run(self):
        for k in self.keys:
            directinput.press(k)
        # infinite loop to indicate that the objective isn't done until task is canceled
        await sleep_forever()

    async def cleanup(self, exception):
        for k in self.keys[::-1]:
            directinput.release(k)


class FaceDirectionObjective(Objective):
    def __init__(self, direction):
        self.direction = direction

    async def run(self):
        async with server.player_status_stream() as stream:
            await face_direction(self.direction, stream)


class MoveNTilesObjective(Objective):
    def __init__(self, direction, n):
        self.direction = direction
        self.n = n

    async def run(self):
        async with server.player_status_stream(ticks=1) as stream:
            status = await stream.current()
            await ensure_not_moving(stream)
            from_x, from_y = status["tileX"], status["tileY"]
            to_x, to_y = from_x, from_y
            if self.direction == "north":
                to_y -= self.n
            elif self.direction == "east":
                to_x += self.n
            elif self.direction == "south":
                to_y += self.n
            elif self.direction == "west":
                to_x -= self.n
            else:
                raise ValueError(f"Unexpected direction {self.direction}")
            path = await path_to_position(to_x, to_y)
            server.log(path.tiles)
            await pathfind_to_position(path, status['location'], stream)

    async def cleanup(self, exception):
        if exception:
            async with server.player_status_stream() as stream:
                await ensure_not_moving(stream)


class MoveToLocationObjective(Objective):
    # def __init__(self, x, y, location):
    def __init__(self):
        x, y, location = 68, 17, "Farm"
        self.x = x
        self.y = y
        self.location = location

    async def run(self):
        async with server.player_status_stream() as stream:
            await ensure_not_moving(stream)
            route = await request_route(self.location, self.x, self.y)
            for i, location in enumerate(route[:-1]):
                next_location = route[i + 1]
                server.log(f"Getting path to next location {next_location}")
                path = await path_to_warp(next_location)
                await pathfind_to_warp(path, location, next_location, stream)

            path = await path_to_position(self.x, self.y)
            await pathfind_to_position(path, route[-1], stream)

    async def cleanup(self, exception):
        if exception:
            async with server.player_status_stream() as stream:
                await ensure_not_moving(stream)


class Route:
    def __init__(self, mod_paths):
        self.paths = tuple(Path(p) for p in mod_paths)


class Path:
    def __init__(self, mod_path):
        tiles = []
        self.tile_indices = {}
        for i, mod_tile in enumerate(mod_path):
            tile = (mod_tile["X"], mod_tile["Y"])
            tiles.append(tile)
            self.tile_indices[tile] = i
        self.tiles = tuple(tiles)


async def request_route(location: str, x: int, y: int):
    route = await server.request("ROUTE", {"toLocation": location})
    if route is None:
        raise RuntimeError(f"Cannot pathfind to {x}, {y} at location {location}")
    return route


async def path_to_warp(location: str):
    path = await server.request("PATH_TO_WARP", {"toLocation": location})
    if path is None:
        raise RuntimeError(f"Cannot pathfind to warp to location {location}")
    return Path(path)


async def path_to_position(x, y):
    path = await server.request("PATH_TO_POSITION", {"x": x, "y": y})
    if path is None:
        raise RuntimeError(f"Cannot pathfind to {x}, {y} to location {location}")
    return Path(path)


async def pathfind_to_warp(
    path: Path,
    location: str,
    next_location: str,
    status_stream: server.Stream,
):
    is_done = False
    while not is_done:
        player_status = await status_stream.next()
        current_location = player_status["location"]
        if current_location != location:
            if current_location == next_location:
                break
            raise RuntimeError(
                f"Unexpected location {current_location}, pathfinding for {location}"
            )
        is_done = move_along_path(path, player_status)
    stop_moving()


async def pathfind_to_position(
    path: Path,
    location: str,
    status_stream: server.Stream,
):
    # warped_task = server.create_stream_next_task(warped_stream.next())
    is_done = False
    while not is_done:
        player_status = await status_stream.next()
        current_location = player_status["location"]
        if current_location != location:
            raise RuntimeError(
                f"Unexpected location {current_location}, pathfinding for {location}"
            )
        is_done = move_along_path(path, player_status)
    stop_moving()

async def pathfind_to_adjacent(x, y, status_stream: server.Stream):
    player_status = await status_stream.next()
    current_tile = player_status["tileX"], player_status["tileY"]
    adjacent_tiles = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
    adjacent_tiles.sort(key=lambda t: distance_between_tiles(current_tile, t))
    potential_paths = []
    for adjacent_tile in adjacent_tiles:
        try:
            path = path_to_position(adjacent_tile[0], adjacent_tile[1])
        except RuntimeError:
            pass
    if not potential_paths:
        raise RuntimeError(f"No path found adjacent to {x}, {y}")
    adjacent_tiles.sort(key=lambda t: distance_between_tiles(current_tile, t))
    
def distance_between_tiles(t1, t2):
    # pathfinding doesn't move diagonally for simplicity so just sum differences between x and y
    return abs(t1[0] - t2[0]) + abs(t1[1] - t2[1]) 


def move_along_path(path, player_status):
    """Return False to continue, True when done"""
    current_position = player_status["position"]
    current_tile = player_status["tileX"], player_status["tileY"]
    current_tile_index = path.tile_indices[current_tile]
    try:
        target_tile = path.tiles[current_tile_index + 1]
    except IndexError:
        # Last tile, all done!
        if player_status["isMoving"] and facing_tile_center(player_status):
            return False
        return True
    direction_to_move = direction_from_tiles(current_tile, target_tile)
    # Rule out not moving, moving in the same direction as next tile, and moving in the opposite direction
    current_direction = player_status["facingDirection"]
    turn_coming = (
        player_status["isMoving"]
        and abs(current_direction - direction_to_move) % 2 == 1
    )
    if turn_coming and facing_tile_center(player_status):
        return False
    start_moving(direction_to_move)


def direction_from_tiles(tile, target_tile):
    if tile[1] - 1 == target_tile[1]:
        return constants.NORTH
    elif tile[0] + 1 == target_tile[0]:
        return constants.EAST
    elif tile[1] + 1 == target_tile[1]:
        return constants.SOUTH
    elif tile[0] - 1 == target_tile[0]:
        return constants.WEST
    else:
        raise RuntimeError(f"Points are incorrect: {tile}, {target_tile}")


def facing_tile_center(player_status):
    """Keep moving towards center of tile before a turn for smoother pathfinding"""
    tile_size = 64  # TODO: get this info from the mod
    position = player_status["position"]
    tile_x, tile_y = player_status["tileX"], player_status["tileY"]
    # x rounds to the nearest tile, y rounds down unless above (or at?) .75, e.g. (21.68, 17.68) becomes (22, 17) and (21.44, 17.77) becomes (21, 18).
    # Normalize so greater than 0 means right/below the center and less than 0 means left/above
    x, y, = (
        position["x"] / tile_size - tile_x,
        position["y"] / tile_size - tile_y - 0.25,
    )
    assert -0.5 <= x <= 0.5
    assert -0.5 <= y <= 0.5
    current_direction = player_status["facingDirection"]
    # start turning when at least 45% into the tile
    offset_from_mid = 0.05
    if current_direction == constants.NORTH:
        return y + offset_from_mid <= 0
    if current_direction == constants.EAST:
        return x + offset_from_mid <= 0
    if current_direction == constants.SOUTH:
        return y - offset_from_mid >= 0
    if current_direction == constants.WEST:
        return x - offset_from_mid >= 0
    return False


def start_moving(direction: int):
    key_to_press = nums_to_keys[direction]
    to_release = "wasd".replace(key_to_press, "")
    for key in to_release:
        if key in directinput.HELD:
            directinput.release(key)
    if key_to_press not in directinput.HELD:
        directinput.press(key_to_press)


async def ensure_moving(direction: int, stream: server.Stream):
    player_status = await stream.current()
    if direction != player_status["facingDirection"]:
        await ensure_not_moving(stream)
        player_status = await stream.current()
    if not player_status["isMoving"]:
        key_to_press = nums_to_keys[direction]
        directinput.press(key_to_press)
        await stream.wait(lambda x: x["isMoving"])


async def sleep_forever():
    while True:
        await asyncio.sleep(3600)


def stop_moving():
    to_release = "wasd"
    for key in to_release:
        if key in directinput.HELD:
            directinput.release(key)


async def ensure_not_moving(stream: server.Stream):
    stop_moving()
    await stream.wait(lambda status: not status["isMoving"])


async def face_direction(direction: int, stream: server.Stream):
    await ensure_not_moving(stream)
    await server.request("FACE_DIRECTION", direction)
    await stream.wait(lambda s: s["facingDirection"] == direction)


async def cancel_active_objective():
    global active_objective
    if active_objective:
        active_objective.run_task.cancel()
        await active_objective.full_task
    active_objective = None


async def new_active_objective(new_objective: Objective):
    global active_objective
    global pending_objective
    pending_objective = new_objective
    await cancel_active_objective()
    if new_objective is pending_objective:
        pending_objective = None
        active_objective = new_objective
        await new_objective.wrap_run()


direction_keys = {
    "north": "w",
    "east": "d",
    "south": "s",
    "west": "a",
}
direction_nums = {
    "north": 0,
    "east": 1,
    "south": 2,
    "west": 3,
}
nums_to_keys = {
    0: "w",
    1: "d",
    2: "s",
    3: "a",
}
directions = {k: k for k in direction_keys}


repeat_mapping = {}



game_state = GameState()





def rule_builder():
    server.setup_async_loop()
    builder = rules.RuleBuilder()
    builder.basic.append(
        rules.ParsedRule(
            mapping=non_repeat_mapping,
            name="stardew_non_repeat",
            extras=[
                rules.num,
                Choice("direction_keys", direction_keys),
                Choice("direction_nums", direction_nums),
                Choice("directions", directions),
            ],
            defaults={"n": 1},
        )
    )
    # builder.repeat.append(
    #     rules.ParsedRule(mapping=repeat_mapping, name="stardew_repeat")
    # )
    return builder


def objective_action(objective_cls, *args):
    format_args = lambda **kw: [objective_cls(*[kw[a] for a in args])]
    return server.AsyncFunction(new_active_objective, format_args=format_args)


non_repeat_mapping = {
    "<direction_keys>": objective_action(HoldKeyObjective, "direction_keys"),
    "face <direction_nums>": objective_action(FaceDirectionObjective, "direction_nums"),
    "stop": server.AsyncFunction(cancel_active_objective, format_args=lambda **kw: []),
    "tool": Function(lambda: directinput.send("c")),
    "(action|check)": Function(lambda: directinput.send("x")),
    "(escape | menu)": Function(lambda: directinput.send("esc")),
    "<n> <directions>": objective_action(MoveNTilesObjective, "directions", "n"),
    "go to mailbox": objective_action(MoveToLocationObjective),
}