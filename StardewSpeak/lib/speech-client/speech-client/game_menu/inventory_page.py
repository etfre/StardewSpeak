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

async def click_trash_can():
    page = await get_inventory_page()
    await menu_utils.click_component(page['trashCan'])


async def focus_item(new_row, new_col):
    page = await get_inventory_page()
    menu = page['inventory']
    await inventory_wrapper.focus_box(menu, new_row, new_col)

async def click_equipment_icon(item):
    page = await get_inventory_page()
    cmp = menu_utils.find_component_by_field(page['equipmentIcons'], 'name', item["name"])
    await menu_utils.focus_component(cmp)
    with server.player_items_stream() as stream:
        player_items = await stream.next()
    if player_items['cursorSlotItem'] and not player_items['equippedItems'][item['field']]:
        await menu_utils.click_component(cmp)
    else:
        await menu_utils.focus_component(cmp)

mapping = {
    "item <positive_index>": df_utils.async_action(focus_item, None, 'positive_index'),
    "row <positive_index>": df_utils.async_action(focus_item, 'positive_index', None),
    "trash can": df_utils.async_action(click_trash_can),
    "<equipment_icons>": df_utils.async_action(click_equipment_icon, 'equipment_icons'),
}

equipment_icons = {
    "boots": {"name": "Boots", "field": "boots"},
    "hat": {"name": "Hat", "field": "hat"},
    "pants": {"name": "Pants", "field": "pants"},
    "left ring | ring one": {"name": "Left Ring", "field": "leftRing"},
    "right ring | ring to": {"name": "Right Ring", "field": "rightRing"},
    "shirt": {"name": "Shirt", "field": "shirt"},
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
            df.Choice('equipment_icons', equipment_icons)
        ],
        defaults={'positive_num': 1},
        context=is_active,
    )
    grammar.add_rule(main_rule)
    grammar.load()
