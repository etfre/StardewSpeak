import game, server
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
    menu = await game.get_active_menu()
    if not menu or menu['menuType'] != 'itemsToGrabMenu':
        return
    submenu = menu[submenu_name]
    if submenu['containsMouse']:
        return
    rows = list_of_rows(submenu['inventory'])
    row, col = item_grab[submenu_name]
    cmp = rows[row][col]
    await focus_component(cmp)

async def focus_component(cmp):
    x, y = cmp['center']
    await server.set_mouse_position(x, y)

async def focus_item(new_row, new_col):
    menu = await game.get_active_menu()
    if not menu or 'menuType' not in menu:
        return
    if menu['menuType'] == "itemsToGrabMenu":
        submenu_name = 'itemsToGrabMenu' if menu['itemsToGrabMenu']['containsMouse'] else 'inventoryMenu'
        submenu = menu[submenu_name]
        rows = list_of_rows(submenu['inventory'])
        indices = find_component_containing_mouse(rows)
        row, col = indices if indices else item_grab[submenu_name]
        if new_row is not None:
            row = new_row
        if new_col is not None:
            col = new_col
        cmp = rows[row][col]
        await focus_component(cmp)
        item_grab[submenu_name] = row, col

def find_component_containing_mouse(list_of_cmp_rows):
    for row_num, row in enumerate(list_of_cmp_rows):
        for col_num, cmp in enumerate(row):
            if cmp['containsMouse']:
                return row_num, col_num

def list_of_rows(cmps):
    '''
    Use center y property to create a list of rows from top to bottom. Assumes all items in a row
    have the same y value
    '''
    rows = []
    for cmp in sorted(cmps, key=lambda c: c['center'][1]):
        if not rows or cmp['center'][1] > rows[-1][-1]['center'][1]:
            rows.append([])
        rows[-1].append(cmp)
    return rows

