import game, server, menu_utils, df_utils
import dragonfly as df

main_button_choice = df.Choice("main_buttons", {"new": "New", "load": "Load", "co op": "Co-op", "exit": "Exit"})

TITLE_MENU = 'titleMenu'

async def click_main_button(btn_name: str):
    menu = await menu_utils.get_active_menu()
    if not menu or menu['menuType'] != 'titleMenu' or menu['subMenu']:
        raise menu_utils.InvalidMenuOption()
    button = menu_utils.find_component_by_field(menu['buttons'], 'name', btn_name)
    await menu_utils.click_component(button)


def get_submenu(title_menu, menu_type=None):
    submenu = title_menu.get('subMenu')
    if not submenu or (menu_type is not None and submenu['menuType'] != menu_type):
        raise menu_utils.InvalidMenuOption()
    return submenu

async def click_submenu_button(button_name):
    menu_getter = get_submenu
    await menu_utils.click_menu_button(button_name, menu_getter=menu_getter)

mapping = {
    "<main_buttons> game": df_utils.async_action(click_main_button, 'main_buttons'),
}

@menu_utils.valid_menu_test
def is_active():
    menu = game.get_context_menu(TITLE_MENU)
    return menu['subMenu'] is None

def load_grammar():
    grammar = df.Grammar("title_menu")
    main_rule = df.MappingRule(
        name="title_menu_rule",
        mapping=mapping,
        extras=[
            main_button_choice,
        ],
        defaults={'positive_num': 1},
        context=is_active,
    )
    grammar.add_rule(main_rule)
    grammar.load()
