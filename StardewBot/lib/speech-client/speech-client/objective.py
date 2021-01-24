# import time
import functools
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
        await game.equip_item(constants.AXE)
        await game.modify_tiles(game.get_trees, game.generic_next_item_key, game.chop_tree_and_gather_resources)
        # async with server.player_status_stream() as stream:
        #     player_status = await stream.next()
        #     start_tile = player_status["tileX"], player_status["tileY"]
        #     while True:
        #         player_status = await stream.next()
        #         current_tile = player_status["tileX"], player_status["tileY"]
        #         trees = await game.get_trees('')
        #         if not trees:
        #             return
        #         tree_path = None
        #         for tree in sorted(trees, key=lambda t: game.score_objects_by_distance(start_tile, current_tile, (t['tileX'], t['tileY']))):
        #             try:
        #                 tree_path = await game.pathfind_to_adjacent(tree['tileX'], tree['tileY'], stream)
        #             except RuntimeError:
        #                 continue
        #             else:
        #                 await game.chop_tree_and_gather_resources()
        #         if not tree_path:
        #             return
class WaterCropsObjective(Objective):

    def __init__(self):
        pass

    async def run(self):
        await game.equip_item(constants.WATERING_CAN)
        async with server.player_status_stream() as stream:
            player_status = await stream.next()
            start_tile = player_status["tileX"], player_status["tileY"]
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

    async def get_debris(self, location):
        objs = await game.get_location_objects(location)
        debris = [o for o in objs if game.is_debris(o)]
        return debris

    async def at_tile(self, obj):
        needed_tool = game.tool_for_object[obj['name']]
        await game.equip_item(needed_tool)
        await game.swing_tool(obj)

    async def run(self):
        await game.modify_tiles(self.get_debris, game.next_debris_key, self.at_tile)
class HoePlotObjective(Objective):

    def __init__(self, n1, n2):
        self.n1 = n1
        self.n2 = n2
        server.log(n1, n2)

    async def run(self):
        async with server.player_status_stream() as stream:
            await game.equip_item(constants.HOE)
            player_status = await stream.next()
        player_tile = player_status["tileX"], player_status["tileY"]
        facing_direction = player_status['facingDirection']
        start_tile = game.next_tile(player_tile, facing_direction)
        plot_tiles = set()
        x_increment = -1 if game.last_faced_east_west == constants.WEST else 1
        y_increment = -1 if game.last_faced_north_south == constants.NORTH else 1
        for i in range(self.n1):
            x = start_tile[0] + i * x_increment
            for j in range(self.n2):
                y = start_tile[1] + j * y_increment
                plot_tiles.add((x, y))
        get_next_diggable = functools.partial(game.get_diggable_tiles, plot_tiles)
        await game.modify_tiles(get_next_diggable, game.generic_next_item_key, game.swing_tool)


class TalkToNPCObjective(Objective):

    def __init__(self, npc_name):
        self.npc_name = npc_name

    async def run(self):
        npc_tile = None
        pathfind_task = None
        async with server.characters_at_location_stream() as npc_stream, server.player_status_stream() as player_stream:
            while pathfind_task is None or not pathfind_task.done():
                npc = await game.find_npc_by_name(self.npc_name, npc_stream)
                next_npc_tile = npc['tileX'], npc['tileY']
                if npc_tile != next_npc_tile:
                    if pathfind_task:
                        await server.cancel_task(pathfind_task)
                    npc_tile = next_npc_tile
                    pathfind_task = server.loop.create_task(game.pathfind_to_adjacent(npc_tile[0], npc_tile[1], player_stream))
            await game.do_action()



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