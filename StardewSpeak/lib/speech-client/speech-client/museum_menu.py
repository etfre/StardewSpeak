import game, server, menu_utils, df_utils, items, objective
from srabuilder import rules
import functools
import dragonfly as df

MUSEUM_MENU = 'museumMenu'

async def get_museum_menu():
    menu = await menu_utils.get_active_menu(menu_type=MUSEUM_MENU)
    return menu

async def drop_item():
    menu = await get_museum_menu()
    await menu_utils.click_component(menu['dropItemInvisibleButton'])

async def move_cursor_tile(direction, amount):
    await game.move_mouse_in_direction(direction, amount * 64)

mapping = {
    **menu_utils.inventory_commands(menu_getter=get_museum_menu),
    "pan <direction_keys>": objective.objective_action(objective.HoldKeyObjective, "direction_keys"),
    "<direction_nums> <positive_num>": df_utils.async_action(move_cursor_tile, "direction_nums", "positive_num"),
}

@menu_utils.valid_menu_test
def is_active():
    menu = game.get_context_menu(MUSEUM_MENU)

def load_grammar():
    grammar = df.Grammar("museum_menu")
    main_rule = df.MappingRule(
        name="museum_menu_rule",
        mapping=mapping,
        extras=[
            df_utils.positive_index,
            df_utils.positive_num,
            df.Choice("direction_keys", game.direction_keys),
            df.Choice("direction_nums", game.direction_nums),
        ],
        context=is_active
    )
    grammar.add_rule(main_rule)
    grammar.load()