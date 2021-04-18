import time
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

from srabuilder.actions import directinput, pydirectinput
import constants, server, game, objective, locations, items, container_menu, title_menu, menu_utils, fishing_menu, letters, new_game_menu, df_utils, characters

mouse_directions = {
    "up": constants.NORTH,
    "right": constants.EAST,
    "down": constants.SOUTH,
    "left": constants.WEST,
}

numrep2 = Sequence(
    [Choice(None, rules.nonZeroDigitMap), Repetition(Choice(None, rules.digitMap), min=0, max=10)],
    name="n2",
)
num2 = Modifier(numrep2, rules.parse_numrep)

async def move_mouse_by_tile(direction, n):
    await game.move_mouse_in_direction(direction, n * 64)

def rule_builder():
    server.setup_async_loop()
    builder = rules.RuleBuilder()
    builder.basic.append(
        rules.ParsedRule(
            mapping=non_repeat_mapping,
            name="stardew_non_repeat",
            extras=[
                rules.num,
                df_utils.positive_num,
                df_utils.positive_index,
                num2,
                Choice("direction_nums", game.direction_nums),
                Choice("npcs", characters.npcs),
                Choice("mouse_directions", mouse_directions),
                Choice("locations", locations.commands(locations.locations)),
                Choice("points", locations.commands(locations.points)),
                title_menu.main_button_choice,
            ],
            defaults={"n": 1, 'positive_num': 1, 'positive_index': 0},
        )
    )
    return builder

non_repeat_mapping = {
    "face <direction_nums>": objective.objective_action(objective.FaceDirectionObjective, "direction_nums"),
    "stop": df_utils.async_action(server.stop_everything),
    "swing": df_utils.async_action(game.press_key, constants.USE_TOOL_BUTTON),
    "(action | check)": df_utils.async_action(game.press_key, constants.ACTION_BUTTON),
    "(escape | menu)": Function(lambda: pydirectinput.press(["esc"])),
    "next toolbar": Function(lambda: pydirectinput.press(["tab"])),
    # "go to mailbox": objective.objective_action(objective.MoveToPointObjective),
    "go to <locations>": objective.objective_action(objective.MoveToLocationObjective, "locations"),
    "<points>": objective.function_objective(objective.move_to_point, "points"),
    "chop trees": objective.objective_action(objective.ChopTreesObjective),
    "start planting": objective.objective_action(objective.PlantSeedsOrFertilizerObjective),
    "clear debris": objective.objective_action(objective.ClearDebrisObjective),
    "attack": objective.objective_action(objective.AttackObjective),
    "defend": objective.objective_action(objective.DefendObjective),
    "(hoe | dig) <n> by <n2>": objective.objective_action(objective.HoePlotObjective, "n", "n2"),
    "talk to <npcs>": objective.objective_action(objective.TalkToNPCObjective, "npcs"),
    "refill watering can": objective.function_objective(game.refill_watering_can),
    "gather crafting": objective.function_objective(game.gather_crafted_items),
    "forage": objective.function_objective(game.gather_forage_items),
    "gather (objects | items)": objective.function_objective(game.gather_objects),
    "dig (artifact | artifacts)": objective.function_objective(game.dig_artifacts),
    "go inside": objective.function_objective(game.go_inside),
    "pet animals": objective.function_objective(objective.pet_animals),
    "milk animals": objective.function_objective(objective.use_tool_on_animals, constants.MILK_PAIL),
    "click [<positive_num>]": df_utils.async_action(server.mouse_click, "left", "positive_num"),
    "right click [<positive_num>]": df_utils.async_action(server.mouse_click, "right", "positive_num"),
    "mouse <mouse_directions> [<positive_num>]": df_utils.async_action(move_mouse_by_tile, 'mouse_directions', 'positive_num'),
    "small mouse <mouse_directions> [<positive_num>]": df_utils.async_action(game.move_mouse_in_direction, 'mouse_directions', 'positive_num'),
    "start fishing": objective.function_objective(fishing_menu.start_fishing),
    "catch fish": df_utils.async_action(fishing_menu.catch_fish),
    "write game state": df_utils.async_action(game.write_game_state),
}