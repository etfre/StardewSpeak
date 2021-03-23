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
import constants, server, game, objective, locations, items, container_menu, title_menu, menu_utils, fishing_menu, letters, new_game_menu, df_utils


tools = {
    "axe": constants.AXE,
    "fishing (rod | pole)": constants.FISHING_ROD,
    "hoe": constants.HOE,
    "pickaxe": constants.PICKAXE,
    "scythe": constants.SCYTHE,
    "watering can": constants.WATERING_CAN,
    "milk pail": constants.MILK_PAIL,
    "pan": constants.PAN,
    "shears": constants.SHEARS,
}
mouse_directions = {
    "up": constants.NORTH,
    "right": constants.EAST,
    "down": constants.SOUTH,
    "left": constants.WEST,
}

npcs = {
    'abigail': constants.ABIGAIL,
    'alex': constants.ALEX,
    'birdie': constants.BIRDIE,
    '[the] bouncer': constants.BOUNCER,
    'caroline': constants.CAROLINE,
    'clint': constants.CLINT,
    'demetrius': constants.DEMETRIUS,
    '[the] dwarf': constants.DWARF,
    'elliott': constants.ELLIOTT,
    'emily': constants.EMILY,
    'evelyn': constants.EVELYN,
    'george': constants.GEORGE,
    'gil': constants.GIL,
    '[the] governor': constants.GOVERNOR,
    'grandpa': constants.GRANDPA,
    'gunther': constants.GUNTHER,
    'gus': constants.GUS,
    'haley': constants.HALEY,
    'harvey': constants.HARVEY,
    'jas': constants.JAS,
    'jodi': constants.JODI,
    'kent': constants.KENT,
    'krobus': constants.KROBUS,
    'leah': constants.LEAH,
    'leo': constants.LEO,
    '[mayor] lewis': constants.LEWIS,
    'linus': constants.LINUS,
    'marlon': constants.MARLON,
    'marnie': constants.MARNIE,
    '(muh roo | mar oo)': constants.MARU,
    'morris': constants.MORRIS,
    'mister (kwee | key)': constants.MR_QI,
    'pam': constants.PAM,
    'penny': constants.PENNY,
    'pierre': constants.PIERRE,
    'professor snail': constants.PROFESSOR_SNAIL,
    'robin': constants.ROBIN,
    'sam': constants.SAM,
    'sandy': constants.SANDY,
    'sebastian': constants.SEBASTIAN,
    'shane': constants.SHANE,
    'vincent': constants.VINCENT,
    'willy': constants.WILLY,
    '[the] wizard': constants.WIZARD,
}


numrep2 = Sequence(
    [Choice(None, rules.nonZeroDigitMap), Repetition(Choice(None, rules.digitMap), min=0, max=10)],
    name="n2",
)
num2 = Modifier(numrep2, rules.parse_numrep)

async def move_mouse(direction, n):
    await game.move_mouse_in_direction(direction, n * 8)

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
                Choice("tools", tools),
                Choice("npcs", npcs),
                Choice("mouse_directions", mouse_directions),
                Choice("locations", locations.commands(locations.locations)),
                Choice("points", locations.commands(locations.points)),
                title_menu.main_button_choice,
            ],
            defaults={"n": 1, 'positive_num': 1, 'positive_index': 0},
        )
    )
    # builder.repeat.append(
    #     rules.ParsedRule(mapping=repeat_mapping, name="stardew_repeat")
    # )
    return builder

non_repeat_mapping = {
    "face <direction_nums>": objective.objective_action(objective.FaceDirectionObjective, "direction_nums"),
    "stop": df_utils.async_action(server.stop_everything),
    "swing": df_utils.async_action(game.press_key, constants.USE_TOOL_BUTTON),
    "(action|check)": df_utils.async_action(game.press_key, constants.ACTION_BUTTON),
    "(escape | menu)": Function(lambda: pydirectinput.press(["esc"])),
    "next toolbar": Function(lambda: pydirectinput.press(["tab"])),
    # "go to mailbox": objective.objective_action(objective.MoveToPointObjective),
    "go to <locations>": objective.objective_action(objective.MoveToLocationObjective, "locations"),
    "<points>": objective.function_objective(objective.move_to_point, "points"),
    "chop trees": objective.objective_action(objective.ChopTreesObjective),
    "start planting": objective.objective_action(objective.PlantSeedsOrFertilizerObjective),
    "clear debris": objective.objective_action(objective.ClearDebrisObjective),
    "defend": objective.objective_action(objective.DefendObjective),
    "hoe <n> by <n2>": objective.objective_action(objective.HoePlotObjective, "n", "n2"),
    "equip <tools>": df_utils.async_action(game.equip_item_by_name, 'tools'),
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
    "mouse <mouse_directions> [<positive_num>]": df_utils.async_action(move_mouse, 'mouse_directions', 'positive_num'),
    "start fishing": df_utils.async_action(fishing_menu.start_fishing),
    "catch fish": df_utils.async_action(fishing_menu.catch_fish),
    "write game state": df_utils.async_action(game.write_game_state),
}