import dragonfly as df
from srabuilder import rules
import title_menu, menu_utils, server, df_utils, game, container_menu

prev_for_sale_index = 0
inventory_wrapper = menu_utils.InventoryMenuWrapper()

async def get_shop_menu():
    return await menu_utils.get_active_menu('shopMenu')

async def focus_menu_section(submenu_name: str):
    assert submenu_name in ('inventory', 'forSale')
    menu = await get_shop_menu()
    for_sale_focused = any(x['containsMouse'] for x in menu['forSaleButtons'])
    if submenu_name == 'forSale' and not for_sale_focused:
        await focus_for_sale_index(prev_for_sale_index)
    elif submenu_name == 'inventory':
        await inventory_wrapper.focus_previous(menu['inventory'])

async def focus_item(idx, key):
    menu = await get_shop_menu()
    inventory = menu['inventory']
    if not inventory['containsMouse'] and key == 'item':
        await focus_for_sale_index(idx)
        return
    row, col = (idx, None) if key == 'row' else (None, idx)
    await inventory_wrapper.focus_box(inventory, row, col)

async def focus_for_sale_index(idx: int):
    global prev_for_sale_index
    menu = await get_shop_menu()
    buttons = menu["forSaleButtons"]
    await menu_utils.focus_component(buttons[idx])
    prev_for_sale_index = 0


async def buy_item_index(idx: int):
    menu = await get_shop_menu()
    buttons = menu["forSaleButtons"]
    await menu_utils.focus_component(buttons[idx])

async def focus_name_box():
    menu = await get_new_game_menu()
    await menu_utils.click_component(menu['nameBoxCC'])



mapping = {
    "item <positive_index>": df_utils.async_action(focus_item, 'positive_index', 'item'),
    "row <positive_index>": df_utils.async_action(focus_item, 'positive_index', 'row'),
    "(shop | store)": df_utils.async_action(focus_menu_section, 'forSale'),
    "backpack": df_utils.async_action(focus_menu_section, 'inventory'),
    **menu_utils.scroll_commands(get_shop_menu),
}

@menu_utils.valid_menu_test
def is_active():
    game.get_context_menu('shopMenu')

def load_grammar():
    grammar = df.Grammar("shop_menu")
    main_rule = df.MappingRule(
        name="shop_menu_rule",
        mapping=mapping,
        extras=[rules.num, df_utils.positive_index, df_utils.positive_num],
        context=is_active,
        defaults={'positive_num': 1},
    )
    grammar.add_rule(main_rule)
    grammar.load()
    