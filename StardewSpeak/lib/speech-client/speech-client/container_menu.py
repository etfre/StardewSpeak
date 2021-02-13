import game, server, menu_utils, df_utils
from srabuilder import rules
import functools
import dragonfly as df

# item_grab_submenu_rule = df.Choice("direction_keys", direction_keys) 

item_grab = {
    'inventoryMenu': menu_utils.InventoryMenuWrapper(),
    'itemsToGrabMenu': menu_utils.InventoryMenuWrapper(),
}

def reset_item_grab_state():
    global item_grab
    item_grab = {
        'inventoryMenu': (0, 0),
        'itemsToGrabMenu': (0, 0),
    }      

async def set_item_grab_submenu(submenu_name: str):
    assert submenu_name in ('inventoryMenu', 'itemsToGrabMenu')
    menu = await menu_utils.get_active_menu('itemsToGrabMenu')
    submenu = menu[submenu_name]
    if submenu['containsMouse']:
        return
    menu_wrapper = item_grab[submenu_name]
    await menu_wrapper.focus_previous(submenu)

async def focus_item(new_row, new_col):
    menu = await menu_utils.get_active_menu(menu_type='itemsToGrabMenu')
    submenu_name = 'itemsToGrabMenu' if menu['itemsToGrabMenu']['containsMouse'] else 'inventoryMenu'
    submenu = menu[submenu_name]
    submenu_wrapper = item_grab[submenu_name]
    await submenu_wrapper.focus_box(submenu, new_row, new_col)

mapping = {
    "item <positive_index>": df_utils.async_action(focus_item, None, 'positive_index'),
    "row <positive_index>": df_utils.async_action(focus_item, 'positive_index', None),
    "inventory": df_utils.async_action(set_item_grab_submenu, 'inventoryMenu'),
    "container": df_utils.async_action(set_item_grab_submenu, 'itemsToGrabMenu'),

}

def is_active():
    return menu_utils.test_menu_type(game.get_context_menu(), 'itemsToGrabMenu')

def load_grammar():
    grammar = df.Grammar("items_to_grab_menu")
    main_rule = df.MappingRule(
        name="items_to_grab_menu_rule",
        mapping=mapping,
        extras=[rules.num, df_utils.positive_index],
        context=df.FuncContext(lambda: is_active()),
    )
    grammar.add_rule(main_rule)
    grammar.load()