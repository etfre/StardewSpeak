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

from srabuilder.actions import directinput
import constants, server, game, objective, locations, container_menu, title_menu, menu_utils, fishing_menu, letters, new_game_menu


direction_keys = {
    "north": "w",
    "main": "wd",
    "east": "d",
    "floor": "ds",
    "south": "s",
    "air": "as",
    "west": "a",
    "wash": "aw",
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
tools = {
    "axe": constants.AXE,
    "fishing rod": constants.FISHING_ROD,
    "hoe": constants.HOE,
    "pickaxe": constants.PICKAXE,
    "scythe": constants.SCYTHE,
    "watering can": constants.WATERING_CAN,
}
mouse_directions = {
    "up": "up",
    "right": "right",
    "down": "down",
    "left": "left",
}

npcs = {
    'abigail': constants.ABIGAIL,
    'alex': constants.ALEX,
    'caroline': constants.CAROLINE,
    'demetrius': constants.DEMETRIUS,
    'elliott': constants.ELLIOTT,
    'emily': constants.EMILY,
    'gus': constants.GUS,
    'haley': constants.HALEY,
    'harvey': constants.HARVEY,
    'jas': constants.JAS,
    'jodi': constants.JODI,
    'kent': constants.KENT,
    'leah': constants.LEAH,
    'lewis': constants.LEWIS,
    'marnie': constants.MARNIE,
    'muh roo': constants.MARU,
    'pam': constants.PAM,
    'penny': constants.PENNY,
    'pierre': constants.PIERRE,
    'robin': constants.ROBIN,
    'sam': constants.SAM,
    'sebastian': constants.SEBASTIAN,
    'shane': constants.SHANE,
    'vincent': constants.VINCENT,
    'willy': constants.WILLY,
}


numrep2 = Sequence(
    [Choice(None, rules.nonZeroDigitMap), Repetition(Choice(None, rules.digitMap), min=0, max=10)],
    name="n2",
)
num2 = Modifier(numrep2, rules.parse_numrep)

def rule_builder():
    server.setup_async_loop()
    builder = rules.RuleBuilder()
    builder.basic.append(
        rules.ParsedRule(
            mapping=non_repeat_mapping,
            name="stardew_non_repeat",
            extras=[
                rules.num,
                num2,
                Choice("direction_keys", direction_keys),
                Choice("direction_nums", direction_nums),
                Choice("directions", directions),
                Choice("tools", tools),
                Choice("npcs", npcs),
                Choice("mouse_directions", mouse_directions),
                Choice("locations", locations.location_commands(locations.locations)),
                title_menu.main_button_choice,
                letters.letters
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
    return server.AsyncFunction(objective.new_active_objective, format_args=format_args)

def function_objective(async_fn, *args):
    format_args = lambda **kw: [objective.FunctionObjective(async_fn, *[kw[a] for a in args])]
    return server.AsyncFunction(objective.new_active_objective, format_args=format_args)


def format_args(args, **kw):
    formatted_args = []
    for a in args:
        try:
            formatted_arg = kw.get(a, a)
        except TypeError:
            formatted_arg = a
        formatted_args.append(formatted_arg)
    return formatted_args

def sync_action(fn, *args):
    format_args_fn = functools.partial(format_args, args)
    return server.SyncFunction(fn, format_args=format_args_fn)

def async_action(async_fn, *args):
    format_args_fn = functools.partial(format_args, args)
    return server.AsyncFunction(async_fn, format_args=format_args_fn)

non_repeat_mapping = {
    "<direction_keys>": objective_action(objective.HoldKeyObjective, "direction_keys"),
    "face <direction_nums>": objective_action(objective.FaceDirectionObjective, "direction_nums"),
    "stop": async_action(server.stop_everything),
    "swing": Function(lambda: directinput.send("c")),
    "(action|check)": Function(lambda: directinput.send("x")),
    "(escape | menu)": Function(lambda: directinput.send("esc")),
    "<n> <directions>": objective_action(objective.MoveNTilesObjective, "directions", "n"),
    "go to mailbox": objective_action(objective.MoveToPointObjective),
    "go to <locations>": objective_action(objective.MoveToLocationObjective, "locations"),
    "start chopping trees": objective_action(objective.ChopTreesObjective),
    "start planting": objective_action(objective.PlantSeedsOrFertilizerObjective),
    "water crops": objective_action(objective.WaterCropsObjective),
    "clear debris": objective_action(objective.ClearDebrisObjective),
    "hoe <n> by <n2>": objective_action(objective.HoePlotObjective, "n", "n2"),
    "equip <tools>": async_action(game.equip_item, 'tools'),
    "talk to <npcs>": objective_action(objective.TalkToNPCObjective, "npcs"),
    "refill watering can": function_objective(game.refill_watering_can),
    "scroll up": async_action(menu_utils.try_menus, [menu_utils.click_menu_button, title_menu.click_submenu_button], constants.UP_ARROW),
    "scroll down": async_action(menu_utils.try_menus, [menu_utils.click_menu_button, title_menu.click_submenu_button], constants.DOWN_ARROW),
    "click": async_action(server.mouse_click),
    "[<n>] mouse <mouse_directions>": async_action(game.move_mouse_in_direction, 'mouse_directions', 'n'),
    "item <n>": server.AsyncFunction(container_menu.focus_item, format_args=lambda **kw: [None, kw['n'] - 1]),
    "row <n>": server.AsyncFunction(container_menu.focus_item, format_args=lambda **kw: [kw['n'] - 1, None]),
    "inventory": async_action(container_menu.set_item_grab_submenu, 'inventoryMenu'),
    "container": async_action(container_menu.set_item_grab_submenu, 'itemsToGrabMenu'),
    "load game <n>": server.AsyncFunction(title_menu.load_game, format_args=lambda **kw: [kw['n'] - 1]),
    "<main_buttons> game": async_action(title_menu.click_main_button, 'main_buttons'),
    "start fishing": async_action(fishing_menu.start_fishing),
    "catch fish": async_action(fishing_menu.catch_fish),
    "(letter | letters | lowercase) <letters>": Function(lambda **kw: letters.type_letters(kw['letters'])),
    "(capital | uppercase) <letters>": Function(lambda **kw: letters.type_letters(kw['letters'].upper())),
}