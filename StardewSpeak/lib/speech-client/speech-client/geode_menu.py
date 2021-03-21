import game, server, menu_utils, df_utils, items
from srabuilder import rules
import functools
import dragonfly as df

GEODE_MENU = 'geodeMenu'

async def get_geode_menu():
    menu = await menu_utils.get_active_menu(menu_type=GEODE_MENU)
    return menu

async def break_geode():
    menu = await get_geode_menu()
    await menu_utils.click_component(menu['geodeSpot'])

mapping = {
    **menu_utils.inventory_commands(menu_getter=get_geode_menu),
    '(break | crack | process) geode': df_utils.async_action(break_geode)
}

@menu_utils.valid_menu_test
def is_active():
    menu = game.get_context_menu(GEODE_MENU)

def load_grammar():
    grammar = df.Grammar("geode_menu")
    main_rule = df.MappingRule(
        name="geode_menu_rule",
        mapping=mapping,
        extras=[df_utils.positive_index],
        context=is_active
    )
    grammar.add_rule(main_rule)
    grammar.load()