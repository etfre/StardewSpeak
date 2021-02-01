import game, server

item_grab_menu_level = 'inventory' # inventory or items_to_grab
row = 0
col = 0

async def focus_component(cmp):
    x, y = cmp['center']
    await server.set_mouse_position(x, y)

async def focus_item(n):
    menu = await game.get_active_menu()
    if not menu or 'menuType' not in menu:
        return
    if menu['menuType'] == "itemGrabMenu":
        await focus_inventory_row_item(menu["inventory"])
    # await focus_inventory_row_item(menu, n)

async def focus_inventory_row_item(menu):
    await focus_component(menu['inventory'][row])

