import server

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

class InvalidMenuOption(Exception):
    pass