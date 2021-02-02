import game, server, menu_utils
import dragonfly as df

main_button_choice = df.Choice("main_buttons", {"new": "New", "load": "Load"}) 

async def click_main_button(btn_name: str):
    menu = await game.get_active_menu()
    if not menu or menu['menuType'] != 'titleMenu' or menu['subMenu']:
        return
    button = game.find_component_by_field(menu['buttons'], 'name', btn_name)
    await game.click_component(button)
