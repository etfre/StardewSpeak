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

import constants, server, game, objective, locations, items, container_menu, title_menu, menu_utils, fishing_menu, letters, new_game_menu, df_utils, characters

mouse_directions = {
    "up": constants.NORTH,
    "right": constants.EAST,
    "down": constants.SOUTH,
    "left": constants.WEST,
}

async def move_mouse_by_tile(direction, n):
    await game.move_mouse_in_direction(direction, n * 64)

def rule_builder():
    builder = rules.RuleBuilder()
    builder.basic.append(
        rules.ParsedRule(
            mapping=non_repeat_mapping,
            name="stardew_non_repeat",
            extras=[
                df_utils.positive_num,
                Choice("mouse_directions", mouse_directions),
            ],
            defaults={'positive_num': 1},
        )
    )
    return builder

non_repeat_mapping = {
    "click [<positive_num>]": df_utils.async_action(server.mouse_click, "left", "positive_num"),
    "right click [<positive_num>]": df_utils.async_action(server.mouse_click, "right", "positive_num"),
    "mouse <mouse_directions> [<positive_num>]": df_utils.async_action(move_mouse_by_tile, 'mouse_directions', 'positive_num'),
    "small mouse <mouse_directions> [<positive_num>]": df_utils.async_action(game.move_mouse_in_direction, 'mouse_directions', 'positive_num'),
    "write game state": df_utils.async_action(game.write_game_state),
    "(action | check)": df_utils.async_action(game.press_key, constants.ACTION_BUTTON),
    "(escape | [open | close] menu)": df_utils.async_action(game.press_key, constants.MENU_BUTTON),
}