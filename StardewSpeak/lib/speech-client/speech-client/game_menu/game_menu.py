import asyncio
import dragonfly as df
import title_menu, menu_utils, server, df_utils, game, letters

async def get_game_menu():
    return await menu_utils.get_active_menu('gameMenu')

async def focus_box(cmp_name):
    await menu_utils.click_menu_button(cmp_name, menu_getter=get_game_menu)

async def focus_name_box():
    menu = await get_new_game_menu()
    await menu_utils.click_component(menu['nameBoxCC'])

def active_page(menu):
    return menu['pages'][menu['currentTab']]

def get_page_by_name(menu, page_type):
    import server
    page = menu_utils.find_component_by_field(menu['pages'], 'type', page_type)
    is_active = page['type'] == active_page(menu)['type']
    if not is_active:
        raise menu_utils.InvalidMenuOption()
    return page

async def click_tab(tab_name):
    menu = await get_game_menu()
    cmp = menu_utils.find_component_by_field(menu["tabs"], 'name', tab_name)
    await menu_utils.click_component(cmp)

tabs = {
    "inventory": "inventory",
    "skills": "skills",
    "social": "social",
    "map": "map",
    "crafting": "crafting",
    "collections": "collections",
    "options": "options",
    "exit [game]": "exit",
}

mapping = {
    "<tabs>": df_utils.async_action(click_tab, 'tabs'),
}

def is_active():
    menu = game.get_context_menu()
    return menu and menu['menuType'] == 'gameMenu' 

def load_grammar():
    grammar = df.Grammar("game_menu")
    main_rule = df.MappingRule(
        name="game_menu_rule",
        mapping=mapping,
        extras=[
            df.Choice("tabs", tabs),
            df_utils.positive_num,
        ],
        defaults={'positive_num': 1},
        context=df.FuncContext(lambda: is_active()),
    )
    grammar.add_rule(main_rule)
    grammar.load()
