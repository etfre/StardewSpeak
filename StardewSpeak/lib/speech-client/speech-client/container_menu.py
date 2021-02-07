import game, server, menu_utils
import functools
import dragonfly as df

# item_grab_submenu_rule = df.Choice("direction_keys", direction_keys) 

item_grab = {
    'inventoryMenu': (0, 0),
    'itemsToGrabMenu': (0, 0),
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
    rows = menu_utils.list_of_rows(submenu['inventory'])
    row, col = item_grab[submenu_name]
    cmp = rows[row][col]
    await menu_utils.focus_component(cmp)

async def focus_item(new_row, new_col):
    menu = await menu_utils.get_active_menu()
    if not menu or 'menuType' not in menu:
        raise menu_utils.InvalidMenuOption()
    if menu['menuType'] == "itemsToGrabMenu":
        submenu_name = 'itemsToGrabMenu' if menu['itemsToGrabMenu']['containsMouse'] else 'inventoryMenu'
        submenu = menu[submenu_name]

        await focus_inventory_box(
            submenu['inventory'],
            new_row, new_col,
            get_previous=lambda: item_grab[submenu_name],
            set_previous=functools.partial(set_previous_container, submenu_name),
        )

async def focus_inventory_box(cmp_list, new_row, new_col, get_previous=lambda: (0, 0), set_previous=lambda r, c: None):
    rows = menu_utils.list_of_rows(cmp_list)
    indices = menu_utils.find_component_containing_mouse(rows) or get_previous()
    row = indices[0] if new_row is None else new_row
    col = indices[1] if new_col is None else new_col
    cmp = rows[row][col]
    await menu_utils.focus_component(cmp)
    set_previous(row, col)
    
def get_previous_container():
    return item_grab[submenu_name]

def set_previous_container(submenu_name, r, c):
    item_grab[submenu_name] = r, c