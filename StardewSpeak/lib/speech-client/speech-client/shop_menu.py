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
    for_sale_focused = any(x['containsMouse'] for x in menu['forSaleButtons'])
    if for_sale_focused and key == 'item':
        await focus_for_sale_index(idx)
        return
    row, col = (idx, None) if key == 'row' else (None, idx)
    await inventory_wrapper.focus_box(menu['inventory'], row, col)

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
    # "buy <n>": df_utils.async_action(buy_item_index, 'n'),
    "item <n>": server.AsyncFunction(focus_item, format_args=lambda **kw: [kw['n'] - 1, 'item']),
    "row <n>": server.AsyncFunction(focus_item, format_args=lambda **kw: [kw['n'] - 1, 'row']),
    "(shop | store)": df_utils.async_action(focus_for_sale_index, 0),
    # "row <n>": server.AsyncFunction(focus_item, format_args=lambda **kw: [kw['n'] - 1, None]),
}

def is_active():
    return menu_utils.test_menu_type(game.get_context_menu(), 'shopMenu')

def load_grammar():
    grammar = df.Grammar("shop_menu")
    main_rule = df.MappingRule(
        name="shop_menu_rule",
        mapping=mapping,
        extras=[rules.num],
        context=df.FuncContext(lambda: is_active()),
    )
    grammar.add_rule(main_rule)
    grammar.load()
    