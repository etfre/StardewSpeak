# import time
import re
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
import server
from dragonfly import *
import sdv_types
from srabuilder import rules

import logger

import constants, server, game, df_utils, stream, server_requests

active_objective = None
pending_objective = None


def get_active_objective():
    return active_objective


class ObjectiveQueue:
    def __init__(self):
        self.objectives = []

    def clear(self):
        self.objectives.clear()


class ObjectiveFailedError(BaseException):
    pass


class Objective:
    def add_task(self, coro):
        task_wrapper = server.TaskWrapper(coro)
        self.tasks.append(task_wrapper)
        return task_wrapper

    @property
    def tasks(self):
        if not hasattr(self, "_tasks"):
            self._tasks = []
        return self._tasks

    async def run(self):
        raise NotImplementedError

    async def wrap_run(self):
        name = self.fn.__name__ if isinstance(self, FunctionObjective) else self.__class__.__name__
        logger.trace(f"Starting objective {name}")
        self.run_task = server.TaskWrapper(self.run())
        await self.run_task.task
        if self.run_task.exception:
            if isinstance(self.run_task.exception, (Exception, ObjectiveFailedError)):
                logger.trace(f"Objective {name} errored: \n{self.run_task.exception_trace}")
            elif isinstance(self.run_task.exception, asyncio.CancelledError):
                logger.trace(f"Canceling objective {name}")
            await game.release_all_keys()
        else:
            logger.trace(f"Successfully completed objective {name}")
        for task_wrapper in self.tasks:
            await task_wrapper.cancel()

    def fail(self, msg=None):
        if msg is None:
            msg = "Objective {self.__class__.__name__} failed"
        raise ObjectiveFailedError(msg)


class FunctionObjective(Objective):
    def __init__(self, fn, *a, **kw):
        self.fn = fn
        self.a = a
        self.kw = kw

    async def run(self):
        await self.fn(*self.a, **self.kw)

    def __repr__(self):
        return "banana"


class HoldKeyObjective(Objective):
    def __init__(self, keys):
        self.keys = keys

    async def run(self):
        async with game.press_and_release(self.keys):
            # infinite loop to indicate that the objective isn't done until task is canceled
            await server.sleep_forever()


class FaceDirectionObjective(Objective):
    def __init__(self, direction):
        self.direction = direction

    async def run(self):
        async with stream.player_status_stream() as pss:
            await game.face_direction(self.direction, pss, move_cursor=True)


class MoveNTilesObjective(Objective):
    def __init__(self, direction, n):
        self.direction = direction
        self.n = n

    async def run(self):
        async with stream.player_status_stream(ticks=1) as pss:
            await game.move_n_tiles(self.direction, self.n, pss)


class MoveToLocationObjective(Objective):
    def __init__(self, location):
        import locations

        self.location: locations.Location = location

    async def run(self):
        async with stream.player_status_stream() as pss:
            await game.move_to_location(self.location.name, pss)


async def move_to_point(point):
    async with stream.player_status_stream() as pss:
        player_status = await pss.next()
        regex_mismatch = isinstance(point.location, re.Pattern) and not point.location.match(
            player_status["location"]["name"]
        )
        str_mismatch = isinstance(point.location, str) and point.location != player_status["location"]["name"]
        if regex_mismatch or str_mismatch:
            raise game.NavigationFailed(
                f'Currently in {player_status["location"]["name"]} - unable to move to point in location {point.location}'
            )
        await game.navigate_nearest_tile(point.get_tiles, pathfind_fn=point.pathfind_fn)
        if point.on_arrival:
            await point.on_arrival()


class ChopTreesObjective(Objective):
    def __init__(self):
        pass

    async def run(self):
        await game.equip_item_by_name(constants.AXE)
        async for tree in game.navigate_tiles(
            server_requests.get_fully_grown_trees_and_stumps, game.generic_next_item_key
        ):
            await game.equip_item_by_name(constants.AXE)
            await game.chop_tree_and_gather_resources(tree)


class WaterCropsObjective(Objective):
    def __init__(self):
        pass

    async def get_unwatered_crops(self):
        hoe_dirt_tiles = await game.get_hoe_dirt()
        tiles_to_water = [
            hdt for hdt in hoe_dirt_tiles if hdt["crop"] and not hdt["isWatered"] and hdt["needsWatering"]
        ]
        return tiles_to_water

    async def run(self):
        await game.equip_item_by_name(constants.WATERING_CAN)
        async with stream.tool_status_stream() as tss:
            watering_can_status = await tss.next()
            assert watering_can_status
            watering_can_upgrade_level = watering_can_status["upgradeLevel"]
            async for crop in game.navigate_tiles(
                self.get_unwatered_crops,
                game.generic_next_item_key,
                allow_action_on_same_tile=False,
            ):
                await game.equip_item_by_name(constants.WATERING_CAN)
                player_status, unwatered_crops = await asyncio.gather(
                    server_requests.get_player_status(), self.get_unwatered_crops()
                )
                unwatered_crop_tiles = [(x["tileX"], x["tileY"]) for x in unwatered_crops]
                power_level = game.calculate_modifiable_tiles(
                    unwatered_crop_tiles, watering_can_upgrade_level, player_status
                )
                await game.swing_tool(power_level, tool_status_stream=tss)


class HarvestCropsObjective(Objective):
    async def get_harvestable_crops(self):
        hoe_dirt_tiles = await game.get_hoe_dirt()
        harvestable_crop_tiles = [hdt for hdt in hoe_dirt_tiles if hdt["crop"] and hdt["readyForHarvest"]]
        return harvestable_crop_tiles

    async def run(self):
        async for crop in game.navigate_tiles(
            self.get_harvestable_crops, game.generic_next_item_key, items_ok=game.ensure_items_changed
        ):
            await game.do_action()


class ClearOreObjective(Objective):
    async def get_ores(self):
        ore_types = set(
            (95, 843, 844, 25, 75, 76, 77, 816, 817, 818, 819, 8, 10, 12, 14, 6, 4, 2, 751, 849, 290, 850, 764, 765)
        )
        objs = await server_requests.get_location_objects()
        ores = [x for x in objs if x["name"] == "Stone" and x["parentSheetIndex"] in ore_types]
        return ores

    async def at_tile(self, obj: sdv_types.LocationObject):
        await game.equip_item_by_name(constants.PICKAXE)
        await game.clear_object(obj, server_requests.get_location_objects, constants.PICKAXE)

    async def run(self):
        async for debris in game.navigate_tiles(self.get_ores, game.next_debris_key):
            await self.at_tile(debris)


class ClearDebrisObjective(Objective):
    def __init__(self, debris_type):
        self.debris_type = debris_type

    async def get_debris(self):
        debris_objects, resource_clumps, tools = await asyncio.gather(
            self.get_debris_objects(),
            game.get_resource_clump_pieces(),
            game.get_tools(),
        )
        debris = debris_objects + resource_clumps
        clearable_debris = []
        for d in debris:
            required_tool = game.tool_for_object[d["name"]]
            tool = tools.get(required_tool["name"])
            if tool and tool["upgradeLevel"] >= required_tool["level"]:
                clearable_debris.append(d)
        if self.debris_type == constants.STONE:
            clearable_debris = [x for x in clearable_debris if x["name"] in (constants.STONE, constants.BOULDER)]
        elif self.debris_type == constants.TWIG:
            clearable_debris = [
                x for x in clearable_debris if x["name"] in (constants.TWIG, constants.HOLLOW_LOG, constants.STUMP)
            ]
        elif self.debris_type == constants.WEEDS:
            clearable_debris = [x for x in clearable_debris if x["name"] == constants.WEEDS]
        return clearable_debris

    async def get_debris_objects(self):
        objs = await server_requests.get_location_objects()
        debris = [{**o, "type": "object"} for o in objs if game.is_debris(o)]
        return debris

    async def at_tile(self, obj):
        needed_tool = game.tool_for_object[obj["name"]]
        await game.equip_item_by_name(needed_tool["name"])
        if obj["type"] == "object":
            await game.clear_object(obj, self.get_debris_objects, needed_tool["name"])
        else:
            assert obj["type"] == "resource_clump"
            await game.clear_object(obj, game.get_resource_clump_pieces, needed_tool["name"])
        if obj["type"] == "resource_clump":
            await game.gather_items_on_ground(6)

    async def run(self):
        async for debris in game.navigate_tiles(self.get_debris, game.next_debris_key):
            await self.at_tile(debris)


class ClearGrassObjective(Objective):
    async def run(self):
        await game.equip_item_by_name(constants.SCYTHE)
        async for debris in game.navigate_tiles(
            server_requests.get_grass, game.next_debris_key, items_ok=lambda prev, items: True
        ):
            await game.equip_item_by_name(constants.SCYTHE)
            await game.swing_tool()


class PlantSeedsOrFertilizerObjective(Objective):
    def __init__(self):
        pass

    async def get_hoe_dirt(self):
        hoe_dirt_tiles = await game.get_hoe_dirt()
        return [x for x in hoe_dirt_tiles if x["canPlantThisSeedHere"]]

    async def run(self):
        async for hdt in game.navigate_tiles(
            self.get_hoe_dirt, game.generic_next_item_key, items_ok=game.ensure_items_changed
        ):
            await game.do_action()


class HoePlotObjective(Objective):
    def __init__(self, n1, n2):
        self.n1: int = n1
        self.n2: int = n2

    async def run(self):
        async with stream.player_status_stream() as pss:
            await game.equip_item_by_name(constants.HOE)
            player_status = await pss.next()
        player_tile = player_status["tileX"], player_status["tileY"]
        facing_direction = player_status["facingDirection"]
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
        async with stream.tool_status_stream() as tss:
            hoe_status = await tss.next()
            assert hoe_status
            hoe_upgrade_level = hoe_status["upgradeLevel"]
            async for hdt in game.navigate_tiles(
                get_next_diggable,
                game.generic_next_item_key,
                allow_action_on_same_tile=False,
                items_ok=game.ensure_items_changed,
            ):
                await game.equip_item_by_name(constants.HOE)
                player_status, candidate_hoe_dirts = await asyncio.gather(
                    server_requests.get_player_status(), get_next_diggable()
                )
                candidate_hoe_dirt_tiles = [(x["tileX"], x["tileY"]) for x in candidate_hoe_dirts]
                power_level = game.calculate_modifiable_tiles(
                    candidate_hoe_dirt_tiles, hoe_upgrade_level, player_status
                )
                await game.swing_tool(power_level, tool_status_stream=tss)

class TalkToNPCObjective(Objective):
    def __init__(self, npc_name):
        self.npc_name = npc_name

    async def run(self):
        req_data = {"characterType": "npc", "requiredName": self.npc_name}
        req_builder = server.RequestBuilder("GET_NEAREST_CHARACTER", req_data)
        try:
            await game.MoveToCharacter(req_builder, tiles_from_target=2).move()
        except game.NavigationFailed:
            game.show_hud_message(f"{self.npc_name} is not in the current location", 2)
        await game.do_action()


async def use_tool_on_animals(tool: str, animal_type=None):
    await game.equip_item_by_name(tool)
    consecutive_errors = 0
    consecutive_error_threshold = 10
    req_data = {"characterType": "animal", "getBy": "readyForHarvest", "requiredName": None}
    req_builder = server.RequestBuilder("GET_NEAREST_CHARACTER", req_data)
    while True:
        animal = await game.MoveToCharacter(req_builder).move()
        did_use = await game.use_tool_on_animal_by_name(animal["name"])
        if not did_use:
            consecutive_errors += 1
        else:
            consecutive_errors = 0
        if consecutive_errors >= consecutive_error_threshold:
            raise RuntimeError()
        await asyncio.sleep(0.1)


async def start_shopping():
    async with stream.player_status_stream() as pss:
        loc = (await stream.next())["location"]["name"]
        if loc == "AnimalShop":
            tile, facing_direction = (12, 16), constants.NORTH
        elif loc == "Blacksmith":
            tile, facing_direction = (3, 15), constants.NORTH
        elif loc == "FishShop":
            tile, facing_direction = (5, 6), constants.NORTH
        elif loc == "JojaMart":
            tile, facing_direction = (11, 25), constants.WEST
        elif loc == "LibraryMuseum":
            tile, facing_direction = (3, 9), constants.NORTH
        elif loc == "Saloon":
            tile, facing_direction = (10, 20), constants.NORTH
        elif loc == "ScienceHouse":
            tile, facing_direction = (8, 20), constants.NORTH
        elif loc == "SeedShop":
            tile, facing_direction = (4, 19), constants.NORTH
        x, y = tile
        await game.pathfind_to_tile(x, y, stream)
        await game.do_action()


async def pet_animals():
    req_data = {"characterType": "animal", "getBy": "unpet", "requiredName": None}
    req_builder = server.RequestBuilder("GET_NEAREST_CHARACTER", req_data)
    while True:
        try:
            animal = await game.MoveToCharacter(req_builder).move()
        except (game.NavigationFailed, RuntimeError):
            return
        await game.pet_animal_by_name(animal["name"])
        await asyncio.sleep(0.1)


class DefendObjective(Objective):
    async def run(self):
        req_data = {"characterType": "monster", "requiredName": None}
        req_builder = server.RequestBuilder("GET_NEAREST_CHARACTER", req_data)
        player_status_builder = server.RequestBuilder("PLAYER_STATUS")
        batched_request_builder = server.RequestBuilder.batch(player_status_builder, req_builder)
        batched_request_builder.data[1]["data"] = {**req_data, "target": None, "getPath": False}
        await game.equip_melee_weapon()
        async with stream.player_status_stream() as player_stream:
            while True:
                player_status, target = await batched_request_builder.request()
                if not target:
                    return
                player_position = player_status["center"]
                closest_monster_position = target["center"]
                distance_from_monster = game.distance_between_points_diagonal(player_position, closest_monster_position)
                if distance_from_monster > 0:
                    direction_to_face = game.direction_from_positions(player_position, closest_monster_position)
                    await game.face_direction(direction_to_face, player_stream)
                if distance_from_monster < 110:
                    await server.set_mouse_position(
                        closest_monster_position[0], closest_monster_position[1], from_viewport=True
                    )
                    await game.swing_tool()
                await asyncio.sleep(0.1)


class AttackObjective(Objective):
    async def run(self):
        req_data = {"characterType": "monster", "requiredName": None}
        req_builder = server.RequestBuilder("GET_NEAREST_CHARACTER", req_data)

        player_status_builder = server.RequestBuilder("PLAYER_STATUS")
        batched_request_builder = server.RequestBuilder.batch(player_status_builder, req_builder)
        batched_request_builder.data[1]["data"] = {**req_data, "target": None, "getPath": False}
        await game.equip_melee_weapon()
        async with stream.player_status_stream() as player_stream:
            player_position = (await player_status_builder.request())["position"]
            while True:
                try:
                    target = await game.MoveToCharacter(req_builder, tiles_from_target=2, distance=100).move()
                except game.NavigationFailed:
                    await asyncio.sleep(0.1)
                    continue
                if target is None:
                    return
                distance_from_monster = 0
                while distance_from_monster < 110:
                    player_status, target = await batched_request_builder.request()
                    player_position = player_status["center"]
                    closest_monster_position = target["center"]
                    distance_from_monster = game.distance_between_points_diagonal(
                        player_position, closest_monster_position
                    )
                    if distance_from_monster > 0:
                        direction_to_face = game.direction_from_positions(player_position, closest_monster_position)
                        await game.face_direction(direction_to_face, player_stream)
                    await server.set_mouse_position(
                        closest_monster_position[0], closest_monster_position[1], from_viewport=True
                    )
                    await game.swing_tool()
                    await asyncio.sleep(0.1)

    def get_closest_monster(self, resp):
        (
            player_status,
            chars,
        ) = resp
        monsters = [c for c in chars if c["isMonster"]]
        if not monsters:
            raise ValueError("No monsters in current location")
        # get closest visible monster if possible, otherwise closest invisible monster
        key = lambda x: (
            x["isInvisible"],
            game.distance_between_points_diagonal(player_status["position"], (x["tileX"], x["tileY"])),
        )
        closest_monster = min(monsters, key=key)
        return closest_monster


async def cancel_active_objective():
    global active_objective
    if active_objective:
        await active_objective.run_task.cancel()
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


def objective_action(objective_cls, *args):
    format_args = lambda **kw: [objective_cls(*[kw.get(a, a) for a in args])]
    return df_utils.AsyncFunction(new_active_objective, format_args=format_args)


def function_objective(async_fn, *args):
    format_args = lambda **kw: [FunctionObjective(async_fn, *[kw.get(a, a) for a in args])]
    return df_utils.AsyncFunction(new_active_objective, format_args=format_args)


def format_args(args, **kw):
    formatted_args = []
    for a in args:
        try:
            formatted_arg = kw.get(a, a)
        except TypeError:
            formatted_arg = a
        formatted_args.append(formatted_arg)
    return formatted_args
