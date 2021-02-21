import asyncio
import dragonfly as df
import title_menu, menu_utils, server, df_utils, game, letters, items, server
from game_menu import game_menu

inventory_wrapper = menu_utils.InventoryMenuWrapper()

async def get_inventory_page():
    menu = await game_menu.get_game_menu()
    page = game_menu.get_page_by_name(menu, 'inventoryPage')
    return page

async def set_item_grab_submenu(submenu_name: str):
    assert submenu_name in ('inventoryMenu', 'itemsToGrabMenu')
    menu = await menu_utils.get_active_menu('itemsToGrabMenu')
    submenu = menu[submenu_name]
    if submenu['containsMouse']:
        return
    menu_wrapper = item_grab[submenu_name]
    await menu_wrapper.focus_previous(submenu)

# async def focus_item(new_row, new_col):
#     menu = await menu_utils.get_active_menu(menu_type='itemsToGrabMenu')
#     submenu_name = 'itemsToGrabMenu' if menu['itemsToGrabMenu']['containsMouse'] else 'inventoryMenu'
#     submenu = menu[submenu_name]
#     submenu_wrapper = item_grab[submenu_name]
#     await submenu_wrapper.focus_box(submenu, new_row, new_col)


async def focus_item(new_row, new_col):
    page = await get_inventory_page()
    menu = page['inventory']
    server.log('fi', new_row, new_col)
    await inventory_wrapper.focus_box(menu, new_row, new_col)

mapping = {
    "item <positive_index>": df_utils.async_action(focus_item, None, 'positive_index'),
    "row <positive_index>": df_utils.async_action(focus_item, 'positive_index', None),

}

@menu_utils.valid_menu_test
def is_active():
    menu = game.get_context_menu('gameMenu')
    game_menu.get_page_by_name(menu, 'inventoryPage')

def load_grammar():
    grammar = df.Grammar("inventory_page")
    main_rule = df.MappingRule(
        name="inventory_page_rule",
        mapping=mapping,
        extras=[
            df_utils.positive_index,
            items.craftable_items_choice,
        ],
        defaults={'positive_num': 1},
        context=is_active,
    )
    grammar.add_rule(main_rule)
    grammar.load()
