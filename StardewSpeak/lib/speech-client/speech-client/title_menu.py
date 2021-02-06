import game, server, menu_utils
import dragonfly as df

main_button_choice = df.Choice("main_buttons", {"new": "New", "load": "Load", "co op": "Co-op", "exit": "Exit"})

def active_submenu_type(menu):
    if menu is None or menu['menuType'] != 'titleMenu' or not menu.get('subMenu') :
        return
    submenu = menu.get('subMenu')
    if submenu is None:
        return
    return submenu['menuType']

async def click_main_button(btn_name: str):
    menu = await menu_utils.get_active_menu()
    if not menu or menu['menuType'] != 'titleMenu' or menu['subMenu']:
        raise menu_utils.InvalidMenuOption()
    button = menu_utils.find_component_by_field(menu['buttons'], 'name', btn_name)
    await menu_utils.click_component(button)

async def load_game(game_idx: int):
    menu = await get_submenu('loadGameMenu')
    button_index = game_idx - menu['currentItemIndex']
    try:
        btn = menu['slotButtons'][button_index]
    except IndexError:
        return
    await menu_utils.click_component(btn)

async def get_submenu(menuType=None):
    menu = await menu_utils.get_active_menu()
    if not menu or menu['menuType'] != 'titleMenu' or not menu.get('subMenu') :
        raise menu_utils.InvalidMenuOption()
    submenu = menu.get('subMenu')
    if not submenu or (menuType is not None and submenu['menuType'] != menuType):
        raise menu_utils.InvalidMenuOption()
    return submenu

async def click_submenu_button(button_name):
    menu_getter = get_submenu
    await menu_utils.click_menu_button(button_name, menu_getter=menu_getter)