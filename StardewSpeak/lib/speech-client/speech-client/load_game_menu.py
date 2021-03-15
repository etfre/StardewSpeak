import asyncio
import dragonfly as df
import title_menu, menu_utils, server, df_utils, game, letters

LOAD_GAME_MENU = 'loadGameMenu'

async def load_game_menu():
    menu = await menu_utils.get_active_menu(title_menu.TITLE_MENU)
    return title_menu.get_submenu(menu, LOAD_GAME_MENU)

async def load_game(game_idx: int):
    menu = await load_game_menu()
    button_index = game_idx - menu['currentItemIndex']
    try:
        btn = menu['slotButtons'][button_index]
    except IndexError:
        return
    await menu_utils.click_component(btn)

mapping = {
    "load game <positive_index>": df_utils.async_action(load_game, "positive_index"),
    **menu_utils.scroll_commands(load_game_menu)
}

@menu_utils.valid_menu_test
def is_active():
    title_menu.get_submenu(game.get_context_menu(title_menu.TITLE_MENU), LOAD_GAME_MENU)

def load_grammar():
    grammar = df.Grammar("load_game_menu")
    main_rule = df.MappingRule(
        name="load_game_menu_rule",
        mapping=mapping,
        extras=[
            df_utils.positive_index,
            df_utils.positive_num,
        ],
        defaults={'positive_num': 1},
        context=is_active,
    )
    grammar.add_rule(main_rule)
    grammar.load()
