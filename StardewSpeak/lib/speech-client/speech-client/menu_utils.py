import server
import asyncio

async def focus_component(cmp):
    x, y = cmp['center']
    await server.set_mouse_position(x, y)

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

async def click_menu_button(button_property):
    am = await get_active_menu()
    server.log(am, button_property)
    if am is None:
        raise InvalidMenuOption()
    btn = am.get(button_property)
    if btn is None:
        raise InvalidMenuOption()
    await click_component(btn)


def find_component_by_field(list_of_components, field_name, field_value):
    return next((x for x in list_of_components if x.get(field_name) == field_value), None)

async def click_component(cmp):
    await focus_component(cmp)
    await asyncio.sleep(0.1) # TODO some kind of mouse stream
    await server.mouse_click()


async def get_active_menu():
    return await server.request('GET_ACTIVE_MENU')

class InvalidMenuOption(Exception):
    pass