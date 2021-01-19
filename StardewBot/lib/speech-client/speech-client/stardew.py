import time
import contextlib
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
import constants, server, game

active_objective = None
pending_objective = None

class ObjectiveQueue:

    def __init__(self):
        self.objectives = []

    def clear(self):
        self.objectives.clear()

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
        with press_and_release(self.keys):
            # infinite loop to indicate that the objective isn't done until task is canceled
            await server.sleep_forever()

class FaceDirectionObjective(Objective):
    def __init__(self, direction):
        self.direction = direction

    async def run(self):
        async with server.player_status_stream() as stream:
            await game.face_direction(self.direction, stream)


class MoveNTilesObjective(Objective):
    def __init__(self, direction, n):
        self.direction = direction
        self.n = n

    async def run(self):
        async with server.player_status_stream(ticks=1) as stream:
            status = await stream.current()
            await game.ensure_not_moving(stream)
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
            path = await game.path_to_position(to_x, to_y, status['location'])
            server.log(path.tiles)
            await game.pathfind_to_position(path, status['location'], stream)

    async def cleanup(self, exception):
        if exception:
            async with server.player_status_stream() as stream:
                await game.ensure_not_moving(stream)


class MoveToLocationObjective(Objective):
    # def __init__(self, x, y, location):
    def __init__(self):
        x, y, location = 68, 17, "Farm"
        self.x = x
        self.y = y
        self.location = location

    async def run(self):
        async with server.player_status_stream() as stream:
            await game.ensure_not_moving(stream)
            route = await game.request_route(self.location, self.x, self.y)
            for i, location in enumerate(route[:-1]):
                next_location = route[i + 1]
                server.log(f"Getting path to next location {next_location}")
                path = await game.path_to_warp(next_location)
                await game.pathfind_to_warp(path, location, next_location, stream)
            status = await stream.next()
            path = await game.path_to_position(self.x, self.y, status['location'])
            await game.pathfind_to_position(path, route[-1], stream)

    async def cleanup(self, exception):
        if exception:
            async with server.player_status_stream() as stream:
                await game.ensure_not_moving(stream)

class ChopTreesObjective(Objective):

    def __init__(self):
        pass

    async def run(self):
        async with server.player_status_stream() as stream:
            player_status = await stream.next()
            start_tile = player_status["tileX"], player_status["tileY"]
            while True:
                player_status = await stream.next()
                current_tile = player_status["tileX"], player_status["tileY"]
                trees = await game.get_trees('')
                if not trees:
                    return
                target_tree = min(trees, key=lambda t: game.sort_objects_by_distance(start_tile, current_tile, (t['tileX'], t['tileY'])))
                await game.pathfind_to_adjacent(target_tree['tileX'], target_tree['tileY'], stream)
                async with server.on_terrain_feature_list_changed_stream() as terrain_stream:
                    with press_and_release('c'):
                        event = await terrain_stream.next()
                await game.gather_debris(15)

@contextlib.contextmanager
def press_and_release(keys):
    for k in keys:
        directinput.press(k)
    try:
        yield
    except (BaseException, Exception) as e:
        raise e
    finally:
        for k in reversed(keys):
            directinput.release(k)

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
    "start chopping trees": objective_action(ChopTreesObjective),
}