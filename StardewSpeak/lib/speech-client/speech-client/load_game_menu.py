import asyncio
import dragonfly as df
import title_menu, menu_utils, server, df_utils, game, letters

LOAD_GAME_MENU = 'loadGameMenu'

def validate_load_game_menu(menu):
    return title_menu.get_submenu(menu, LOAD_GAME_MENU)

async def go_back(menu):
    await menu_utils.click_component(menu['backButton'])

async def load_game(menu, game_idx: int):
    button_index = game_idx - menu['currentItemIndex']
    try:
        btn = menu['slotButtons'][button_index]
    except IndexError:
        return
    await menu_utils.click_component(btn)

mapping = {
    "[go] back": df_utils.async_action(go_back),
    "(load [game] | [load] game) <positive_index>": df_utils.async_action(load_game, "positive_index"),
    **menu_utils.scroll_commands()
}

def load_grammar():
    grammar = menu_utils.build_menu_grammar("load_game_menu", mapping, validate_load_game_menu, extras=[df_utils.positive_index, df_utils.positive_num])
    grammar.load()
