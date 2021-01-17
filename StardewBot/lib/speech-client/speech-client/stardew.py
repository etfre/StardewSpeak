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

# from actions import directinput
from srabuilder.actions import directinput
import constants

loop = asyncio.new_event_loop()
active_objective = None
pending_objective = None
streams = weakref.WeakValueDictionary()


class GameState:
    def __init__(self):
        self.last_warp = None


class Stream:
    def __init__(self, name, data=None):
        self.has_value = False
        self.latest_value = None
        self.future = loop.create_future()
        self.name = name
        self.id = f"{name}_{str(uuid.uuid4())}"
        self.closed = False
        self.open(data)

    def set_value(self, value):
        self.latest_value = value
        self.has_value = True
        try:
            self.future.set_result(None)
        except asyncio.InvalidStateError:
            pass

    def open(self, data):
        streams[self.id] = self
        send_message(
            "NEW_STREAM",
            {
                "name": self.name,
                "stream_id": self.id,
                "data": data,
            },
        )

    def close(self):
        if not self.closed:
            self.closed = True
            send_message("STOP_STREAM", self.id)
            del streams[self.id]
            self.set_value(None)

    async def current(self):
        if self.has_value:
            return self.latest_value
        return await self.next()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.close()

    async def next(self):
        if self.closed:
            log("Stream is already closed")
            return
        if not self.future.done():
            await self.future
        if self.closed:
            log(f"Stream {self.name} closed while waiting for next value")
            return
        self.future = loop.create_future()
        return self.latest_value


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
        log(f"Starting objective {name}")
        self.run_task = asyncio.create_task(self.run())
        try:
            await self.run_task
        except (Exception, ObjectiveFailedError) as e:
            err = e
            tb = traceback.format_exc()
            log(f"Objective {name} errored: \n{tb}")
        except asyncio.CancelledError as e:
            err = e
            log(f"Canceling objective {name}")
        else:
            err = None
            log(f"Successfully completed objective {name}")
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
        async with player_status_stream() as stream:
            await face_direction(self.direction, stream)


class MoveNTilesObjective(Objective):
    def __init__(self, direction, n):
        self.direction = direction
        self.n = n

    async def run(self):
        async with player_status_stream(ticks=1) as stream:
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
            log(path.tiles)
            await pathfind_to_position(path, status['location'], stream)

    async def cleanup(self, exception):
        if exception:
            async with player_status_stream() as stream:
                await ensure_not_moving(stream)


class MoveToLocationObjective(Objective):
    # def __init__(self, x, y, location):
    def __init__(self):
        x, y, location = 68, 17, "Farm"
        self.x = x
        self.y = y
        self.location = location

    async def run(self):
        async with player_status_stream() as stream:
            await ensure_not_moving(stream)
            route = await request_route(self.location, self.x, self.y)
            for i, location in enumerate(route[:-1]):
                next_location = route[i + 1]
                log(f"Getting path to next location {next_location}")
                path = await path_to_warp(next_location)
                await pathfind_to_warp(path, location, next_location, stream)

            path = await path_to_position(self.x, self.y)
            await pathfind_to_position(path, route[-1], stream)

    async def cleanup(self, exception):
        if exception:
            async with player_status_stream() as stream:
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
    route = await request("ROUTE", {"toLocation": location})
    if route is None:
        raise RuntimeError(f"Cannot pathfind to {x}, {y} at location {location}")
    return route


async def path_to_warp(location: str):
    path = await request("PATH_TO_WARP", {"toLocation": location})
    if path is None:
        raise RuntimeError(f"Cannot pathfind to warp to location {location}")
    return Path(path)


async def path_to_position(x, y):
    path = await request("PATH_TO_POSITION", {"x": x, "y": y})
    if path is None:
        raise RuntimeError(f"Cannot pathfind to {x}, {y} to location {location}")
    return Path(path)


async def pathfind_to_warp(
    path: Path,
    location: str,
    next_location: str,
    status_stream: Stream,
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
    status_stream: Stream,
):
    # warped_task = create_stream_next_task(warped_stream.next())
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

async def pathfind_to_adjacent(x, y, status_stream: Stream):
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


async def ensure_moving(direction: int, stream: Stream):
    player_status = await stream.current()
    if direction != player_status["facingDirection"]:
        await ensure_not_moving(stream)
        player_status = await stream.current()
    if not player_status["isMoving"]:
        key_to_press = nums_to_keys[direction]
        directinput.press(key_to_press)
        await stream_wait(lambda x: x["isMoving"], stream)


def create_stream_next_task(awaitable):
    async def to_call(awaitable):
        try:
            return await awaitable
        except ValueError as e:
            pass

    return loop.create_task(to_call(awaitable))


def player_status_stream(ticks=1):
    return Stream("UPDATE_TICKED", data={"state": "PLAYER_STATUS", "ticks": ticks})


def on_warped_stream(ticks=1):
    return Stream("ON_WARPED", data={"state": "PLAYER_STATUS", "ticks": ticks})


async def sleep_forever():
    while True:
        await asyncio.sleep(3600)


def stop_moving():
    to_release = "wasd"
    for key in to_release:
        if key in directinput.HELD:
            directinput.release(key)


async def ensure_not_moving(stream: Stream):
    stop_moving()
    await stream_wait(lambda status: not status["isMoving"], stream)


async def move_to(location: str, x: int, y: int):
    pass


async def face_direction(direction: int, stream: Stream):
    await ensure_not_moving(stream)
    send_message("FACE_DIRECTION", direction)
    await stream_wait(lambda s: s["facingDirection"] == direction, stream)


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


async def stream_wait(condition, stream: Stream):
    item = await stream.current()
    while not condition(item):
        item = await stream.next()
    return item


class AsyncFunction(ActionBase):
    def __init__(self, coro, format_args=None):
        super().__init__()
        self.coro = coro
        self.format_args = format_args

    def execute(self, data=None):
        assert isinstance(data, dict)
        kwargs = {k: v for k, v in data.items() if not k.startswith("_")}
        if self.format_args:
            args = self.format_args(**kwargs)
            return call_soon(self.coro, *args)
        return call_soon(self.coro, **kwargs)


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


def call_soon(coro, *args, **kw):
    loop.call_soon_threadsafe(_do_create_task, coro, *args, **kw)


def _do_create_task(coro, *args, **kw):
    loop.create_task(coro(*args, **kw))


repeat_mapping = {}


mod_requests = {}

game_state = GameState()


def setup_async_loop(loop):
    def async_setup(l):
        l.set_exception_handler(exception_handler)
        l.create_task(async_readline())
        l.create_task(heartbeat(60))
        l.run_forever()

    def exception_handler(loop, context):
        # This only works when there are no references to the above tasks.
        # https://bugs.python.org/issue39256y'
        get_engine().disconnect()
        raise context["exception"]

    async_thread = threading.Thread(target=async_setup, daemon=True, args=(loop,))
    async_thread.start()


async def heartbeat(timeout):
    while True:
        fut = request("HEARTBEAT")
        try:
            resp = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError as e:
            raise e
        await asyncio.sleep(timeout)


async def async_readline():
    # Is there a better way to read async stdin on Windows?
    q = queue.Queue()

    def _run(future_queue):
        while True:
            fut = future_queue.get()
            line = sys.stdin.readline()
            loop.call_soon_threadsafe(fut.set_result, line)

    threading.Thread(target=_run, daemon=True, args=(q,)).start()
    while True:
        fut = loop.create_future()
        q.put(fut)
        line = await fut
        on_message(line)


def request(msg_type, msg=None):
    sent_msg = send_message(msg_type, msg)
    fut = loop.create_future()
    mod_requests[sent_msg["id"]] = fut
    return fut


def send_message(msg_type, msg=None):
    msg_id = str(uuid.uuid4())
    full_msg = {"type": msg_type, "id": msg_id, "data": msg}
    print(json.dumps(full_msg), flush=True)
    return full_msg


def on_message(msg_str):
    try:
        msg = json.loads(msg_str)
    except json.JSONDecodeError:
        raise RuntimeError(f"Got invalid message from mod {msg_str}")
    msg_type = msg["type"]
    msg_data = msg["data"]
    if msg_type == "RESPONSE":
        fut = mod_requests.pop(msg_data["id"])
        resp_value = msg_data["value"]
        fut.set_result(resp_value)
    elif msg_type == "STREAM_MESSAGE":
        stream_id = msg_data["stream_id"]
        stream = streams.get(stream_id)
        if stream is None:
            log(f"Can't find {stream_id}")
            send_message("STOP_STREAM", stream_id)
            return
        stream.set_value(msg_data["value"])
        stream.latest_value = msg_data["value"]
        try:
            stream.future.set_result(None)
        except asyncio.InvalidStateError:
            pass
    elif msg_type == "ON_EVENT":
        handle_event(msg_data["eventType"], msg_data["data"])
    else:
        raise RuntimeError(f"Unhandled message type from mod: {msg_type}")


def handle_event(event_type, data):
    if event_type == "ON_WARPED":
        game_state.last_warp = data


def log(msg):
    to_send = msg if isinstance(msg, str) else json.dumps(msg)
    return send_message("LOG", to_send)

def rule_builder():
    setup_async_loop(loop)
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
    return AsyncFunction(new_active_objective, format_args=format_args)


non_repeat_mapping = {
    "<direction_keys>": objective_action(HoldKeyObjective, "direction_keys"),
    "face <direction_nums>": objective_action(FaceDirectionObjective, "direction_nums"),
    "stop": AsyncFunction(cancel_active_objective, format_args=lambda **kw: []),
    "tool": Function(lambda: directinput.send("c")),
    "(action|check)": Function(lambda: directinput.send("x")),
    "(escape | menu)": Function(lambda: directinput.send("esc")),
    "<n> <directions>": objective_action(MoveNTilesObjective, "directions", "n"),
    "go to mailbox": objective_action(MoveToLocationObjective),
}