import game, server, menu_utils
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
    menu = await menu_utils.get_active_menu()
    if not menu or menu['menuType'] != 'itemsToGrabMenu':
        raise menu_utils.InvalidMenuOption()
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
        def get_previous():
            return item_grab[submenu_name]
        def set_previous(r, c):
            item_grab[submenu_name] = r, c
        await focus_inventory_box(submenu['inventory'], new_row, new_col, get_previous, set_previous)
        # rows = menu_utils.list_of_rows(submenu['inventory'])
        # indices = menu_utils.find_component_containing_mouse(rows)
        # row, col = indices if indices else item_grab[submenu_name]
        # if new_row is not None:
        #     row = new_row
        # if new_col is not None:
        #     col = new_col
        # cmp = rows[row][col]
        # await menu_utils.focus_component(cmp)
        # item_grab[submenu_name] = row, col

async def focus_inventory_box(cmp_list, new_row, new_col, get_previous=lambda: (0, 0), set_previous=lambda r, c: None):
    rows = menu_utils.list_of_rows(cmp_list)
    indices = menu_utils.find_component_containing_mouse(rows)
    row, col = indices if indices else get_previous()
    if new_row is not None:
        row = new_row
    if new_col is not None:
        col = new_col
    cmp = rows[row][col]
    await menu_utils.focus_component(cmp)
    set_previous(row, col)