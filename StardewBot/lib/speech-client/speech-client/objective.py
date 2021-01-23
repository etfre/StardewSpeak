# import time
import async_timeout
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
        with game.press_and_release(self.keys):
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
            await game.equip_item(constants.AXE)
            player_status = await stream.next()
            start_tile = player_status["tileX"], player_status["tileY"]
            while True:
                player_status = await stream.next()
                current_tile = player_status["tileX"], player_status["tileY"]
                trees = await game.get_trees('')
                if not trees:
                    return
                tree_path = None
                for tree in sorted(trees, key=lambda t: game.score_objects_by_distance(start_tile, current_tile, (t['tileX'], t['tileY']))):
                    try:
                        tree_path = await game.pathfind_to_adjacent(tree['tileX'], tree['tileY'], stream)
                    except RuntimeError:
                        continue
                    else:
                        async with server.on_terrain_feature_list_changed_stream() as terrain_stream:
                            with game.press_and_release(constants.TOOL_KEY):
                                event = await terrain_stream.next()
                        await game.gather_items_on_ground(15)
                if not tree_path:
                    return
class WaterCropsObjective(Objective):

    def __init__(self):
        pass

    async def run(self):
        async with server.player_status_stream() as stream:
            player_status = await stream.next()
            start_tile = player_status["tileX"], player_status["tileY"]
            await game.equip_item(constants.WATERING_CAN)
            while True:
                hoe_dirt_tiles = await game.get_hoe_dirt('')
                tiles_to_water = [(hdt['tileX'], hdt['tileY']) for hdt in hoe_dirt_tiles if hdt['crop'] and not hdt['isWatered']]
                if not tiles_to_water:
                    return
                player_status = await stream.next()
                current_tile = player_status["tileX"], player_status["tileY"]
                hoe_dirt_path = None
                facing_direction = player_status['facingDirection']
                for tile_x, tile_y in sorted(tiles_to_water, key=lambda t: game.next_crop_key(start_tile, current_tile, t, facing_direction)):
                    try:
                        hoe_dirt_path = await game.pathfind_to_adjacent(tile_x, tile_y, stream)
                    except RuntimeError:
                        continue
                    else:
                        await game.swing_tool()
                        break
                if not hoe_dirt_path:
                    return

class ClearDebrisObjective(Objective):

    def __init__(self):
        pass

    async def run(self):
        async with server.player_status_stream() as stream:
            player_status = await stream.next()
            start_tile = player_status["tileX"], player_status["tileY"]
            await game.equip_item(constants.WATERING_CAN)
            while True:
                objs = await game.get_location_objects('')
                debris = [o for o in objs if game.is_debris(o)]
                if not debris:
                    return
                player_status = await stream.next()
                current_tile = player_status["tileX"], player_status["tileY"]
                path_moved_to_target = None
                facing_direction = player_status['facingDirection']
                for obj in sorted(debris, key=lambda o: game.next_debris_key(start_tile, current_tile, o, facing_direction)):
                    server.log(obj)
                    
                    try:
                        path_moved_to_target = await game.pathfind_to_adjacent(obj['tileX'], obj['tileY'], stream)
                    except RuntimeError:
                        continue
                    else:
                        needed_tool = game.tool_for_object[obj['name']]
                        await game.equip_item(needed_tool)
                        await game.swing_tool()
                        break
                if not path_moved_to_target:
                    return

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