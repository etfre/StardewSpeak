import dragonfly as df
import server, constants
import asyncio

async def focus_component(cmp):
    if not cmp['visible']:
        raise InvalidMenuOption('Cannot focus non-visible component')   
    x, y = cmp['center']
    await server.set_mouse_position(x, y)

def find_component_containing_mouse(list_of_cmp_rows):
    for row_num, row in enumerate(list_of_cmp_rows):
        for col_num, cmp in enumerate(row):
            if cmp['containsMouse']:
                return row_num, col_num

def list_of_rows(cmps, y_threshold=25):
    '''
    Use center y property to create a list of rows from top to bottom. Assumes all items in a row
    have the same y value
    '''
    if not cmps:
        return []
    y_sorted = sorted(cmps, key=lambda c: c['center'][1])
    rows = [[y_sorted[0]]]
    for cmp in y_sorted[1:]:
        cmp_y = cmp['center'][1]
        first_in_row_y = rows[-1][0]['center'][1]
        new_row = cmp_y >= first_in_row_y + y_threshold
        if new_row:
            rows.append([])
        rows[-1].append(cmp)
    return rows

async def get_active_menu(menu_type=None):
    menu = await server.request('GET_ACTIVE_MENU')
    if menu_type is not None:
        if menu is None:
            raise InvalidMenuOption(f'Expecting {menu_type}, got None')
        if menu['menuType'] != menu_type:
            raise InvalidMenuOption(f"Expecting {menu_type}, got {menu['menuType']}")
    return menu


async def click_menu_button(button_property, menu_getter=get_active_menu):
    menu = await menu_getter()
    if menu is None:
        raise InvalidMenuOption()
    btn = menu.get(button_property)
    if btn is None:
        raise InvalidMenuOption()
    await click_component(btn)

def find_component_by_field(list_of_components, field_name, field_value):
    return next((x for x in list_of_components if x.get(field_name) == field_value), None)

async def click_component(cmp):
    await focus_component(cmp)
    await asyncio.sleep(0.1) # TODO some kind of mouse stream
    await server.mouse_click()

async def scroll_up(menu, count=1):
    cmp = menu[constants.UP_ARROW]
    for i in range(count):
        await click_component(cmp)
        await asyncio.sleep(0.1)

async def scroll_down(menu, count=1):
    cmp = menu[constants.DOWN_ARROW]
    for i in range(count):
        await click_component(cmp)
        await asyncio.sleep(0.1)

async def try_menus(try_fns, *a):
    for fn in try_fns:
        try:
            await fn(*a)
        except InvalidMenuOption:
            pass
        else:
            return

def valid_menu_test(fn):
    def test_fn():
        try:
            res = fn()
        except InvalidMenuOption:
            return False
        else:
            return res is not False
    return df.FuncContext(test_fn)

class InventoryMenuWrapper:

    def __init__(self):
        self.row = 0
        self.col = 0

    async def focus_previous(self, inventory_menu):
        await self.focus_box(inventory_menu, self.row, self.col)

    async def focus_box(self, inventory_menu, new_row, new_col):
        rows = list_of_rows(inventory_menu['inventory'])
        indices = find_component_containing_mouse(rows) or (self.row, self.col)
        row = indices[0] if new_row is None else new_row
        col = indices[1] if new_col is None else new_col
        cmp = rows[row][col]
        await focus_component(cmp)
        self.row = row
        self.col = col

    async def focus_box_by_item_name(self, name: str):
        pass

def scroll_commands(menu_getter, page_size=4):
    import df_utils

    async def scroll_up_wrapper(n):
        menu = await menu_getter()
        await scroll_up(menu, n)

    async def scroll_down_wrapper(n):
        menu = await menu_getter()
        await scroll_down(menu, n)

    return {
        "[<positive_num>] scroll up": df_utils.async_action(scroll_up_wrapper, 'positive_num'),
        "[<positive_num>] scroll down": df_utils.async_action(scroll_down_wrapper, 'positive_num'),
        "[<positive_num>] page up": df_utils.AsyncFunction(scroll_up_wrapper, format_args=lambda **kw: [kw['positive_num'] * page_size]),
        "[<positive_num>] page down": df_utils.AsyncFunction(scroll_down_wrapper, format_args=lambda **kw: [kw['positive_num'] * page_size]),
    }

class InvalidMenuOption(Exception):
    pass

def yield_clickable_components(item):
    if isinstance(item, dict):
        if item.get('type') == 'clickableComponent':
            if item['visible']:
                yield item
        else:
            menu_type = item.get('menuType')
            # if menu_type == 'gameMenu':
            #     item = item.copy()
            #     item['pages'] = [item['pages'][item['currentTab']]]
            for child in item.values():
                yield from yield_clickable_components(child)
    if isinstance(item, (list, tuple)):
        for child in item:
            yield from yield_clickable_components(child)

def inventory_commands(menu_getter):
    import df_utils
    inventory_wrapper = InventoryMenuWrapper()
    async def inventory_focus(new_row, new_col):
        menu = await menu_getter() 
        inventory = menu['inventory']
        await inventory_wrapper.focus_box(inventory, new_row, new_col)

    async def click_button(name):
        menu = await menu_getter()
        await click_component(menu[name])

    commands = {
        "item <positive_index>": df_utils.async_action(inventory_focus, None, 'positive_index'),
        "row <positive_index>": df_utils.async_action(inventory_focus, 'positive_index', None),
        "ok": df_utils.async_action(click_button, "okButton"),
        "trash can": df_utils.async_action(click_button, "trashCan"),
    }
    return commands
