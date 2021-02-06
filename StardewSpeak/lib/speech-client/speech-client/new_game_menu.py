import dragonfly as df
import title_menu, menu_utils, server, df_utils, game

async def get_new_game_menu():
    return await title_menu.get_submenu('characterCustomizationMenu')

async def focus_box(cmp_name):
    await menu_utils.click_menu_button(cmp_name, menu_getter=get_new_game_menu)

async def focus_name_box():
    menu = await get_new_game_menu()
    await menu_utils.click_component(menu['nameBoxCC'])


# sleeping = False


# def notify(message):
#     if message == "sleep":
#         print("Sleeping...")
#     elif message == "wake":
#         print("Awake...")

mapping = {
    "name": df_utils.async_action(focus_box, 'nameBoxCC'),
    "farm name": df_utils.async_action(focus_box, 'farmnameBoxCC'),
    "favorite thing": df_utils.async_action(focus_box, 'favThingBoxCC'),
    "(random | [roll] dice)": df_utils.async_action(focus_box, 'randomButton'),
    "(ok [button] | start game)": df_utils.async_action(focus_box, 'okButton'),
}

def is_active():
    menu_type = title_menu.active_submenu_type(game.get_context_menu())
    return menu_type == 'characterCustomizationMenu' 

def load_grammar():
    grammar = df.Grammar("new_game_menu")
    main_rule = df.MappingRule(
        name="new_game_menu_rule",
        mapping=mapping,
        extras=[],
        context=df.FuncContext(lambda: is_active()),
    )
    grammar.add_rule(main_rule)
    grammar.load()
