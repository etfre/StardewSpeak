import game, server, menu_utils
import dragonfly as df

main_button_choice = df.Choice("main_buttons", {"new": "New", "load": "Load", "co op": "Co-op", "exit": "Exit"}) 

async def click_main_button(btn_name: str):
    menu = await menu_utils.get_active_menu()
    if not menu or menu['menuType'] != 'titleMenu' or menu['subMenu']:
        raise menu_utils.InvalidMenuOption()
    button = menu_utils.find_component_by_field(menu['buttons'], 'name', btn_name)
    await menu_utils.click_component(button)

async def load_game(game_idx: int):
    menu = await get_submenu()
    if menu['menuType'] != 'loadGameMenu':
        raise menu_utils.InvalidMenuOption()
    button_index = game_idx + menu['currentItemIndex']
    try:
        btn = menu['slotButtons'][button_index]
    except IndexError:
        return
    await menu_utils.click_component(btn)

async def get_submenu():
    menu = await menu_utils.get_active_menu()
    if not menu or menu['menuType'] != 'titleMenu' or not menu.get('subMenu') :
        raise menu_utils.InvalidMenuOption()
    return menu.get('subMenu')