import asyncio
import dragonfly as df
import title_menu, menu_utils, server, df_utils, game

async def get_new_game_menu():
    return await title_menu.get_submenu('characterCustomizationMenu')

async def focus_box(cmp_name):
    await menu_utils.click_menu_button(cmp_name, menu_getter=get_new_game_menu)

async def focus_name_box():
    menu = await get_new_game_menu()
    await menu_utils.click_component(menu['nameBoxCC'])

async def click_farm(farm):
    menu = await get_new_game_menu()
    cmp = menu_utils.find_component_by_field(menu['farmTypeButtons'], 'name', farm)
    await menu_utils.click_component(cmp)

async def click_arrow_field(field, cmp_list_name, count):
    menu = await get_new_game_menu()
    cmp = menu_utils.find_component_by_field(menu[cmp_list_name], 'name', field)
    for i in range(count):
        await menu_utils.click_component(cmp)
        if i < count - 1:
            await asyncio.sleep(0.1)

farm_types = {
    "standard": "Standard",
    "riverland": "Riverland",
    "forest": "Forest",
    "hill [top]": "Hills",
    "wilderness": "Wilderness",
    "four corners": "Four Corners",
    "beach": "Beach",
}

arrows = {
    "previous": "leftSelectionButtons",
    "next": "rightSelectionButtons",
}
arrow_fields = {
    "(accessory | accessories)": "Acc",  
    "direction": "Direction",  
    "hair": "Hair",  
    "pants": "Pants Style",
    "(pet | animal)": "Pet",
    "shirt": "Shirt",
    "skin": "Skin",
}

mapping = {
    "name": df_utils.async_action(focus_box, 'nameBoxCC'),
    "farm name": df_utils.async_action(focus_box, 'farmnameBoxCC'),
    "favorite thing": df_utils.async_action(focus_box, 'favThingBoxCC'),
    "(random | [roll] dice)": df_utils.async_action(focus_box, 'randomButton'),
    "(ok [button] | start game)": df_utils.async_action(focus_box, 'okButton'),
    "skip (intro | introduction)": df_utils.async_action(focus_box, 'skipIntroButton'),
    "<farm_types> farm": df_utils.async_action(click_farm, 'farm_types'),
    "[<positive_num>] <arrows> <arrow_fields>": df_utils.async_action(click_arrow_field, 'arrow_fields', 'arrows', 'positive_num'),
}

def is_active():
    menu_type = title_menu.active_submenu_type(game.get_context_menu())
    return menu_type == 'characterCustomizationMenu' 

def load_grammar():
    grammar = df.Grammar("new_game_menu")
    main_rule = df.MappingRule(
        name="new_game_menu_rule",
        mapping=mapping,
        extras=[
            df.Choice("farm_types", farm_types),
            df.Choice("arrow_fields", arrow_fields),
            df.Choice("arrows", arrows),
            df_utils.positive_num
        ],
        defaults={'positive_num': 1},
        context=df.FuncContext(lambda: is_active()),
    )
    grammar.add_rule(main_rule)
    grammar.load()
