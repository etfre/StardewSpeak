import dragonfly as df
from srabuilder import rules
import title_menu, menu_utils, server, df_utils, game, container_menu

TITLE_TEXT_INPUT_MENU = 'titleTextInputMenu'

def validate_menu(menu):
    return title_menu.get_submenu(menu, TITLE_TEXT_INPUT_MENU)

async def host_new_farm(menu):
    server.log(menu['currentTab'], level=3)  
    if menu['currentTab'] == "HOST_TAB":
        await menu_utils.click_component(menu['slotButtons'][0])

async def join_lan_game(menu):
    if menu['currentTab'] == "JOIN_TAB":
        await menu_utils.click_component(menu['slotButtons'][0])

async def load_game(menu, game_idx: int):
    if menu['currentTab'] == "HOST_TAB":
        button_index = game_idx + 1 # skip "host new farm" slot
        try:
            btn = menu['slotButtons'][button_index]
        except IndexError:
            return
        await menu_utils.click_component(btn)

mapping = {
    "paste": menu_utils.simple_click("paseButton"),
    "join": menu_utils.simple_click("joinTab"),
    "host new farm": df_utils.async_action(host_new_farm),
    "join lan game": df_utils.async_action(join_lan_game),
    "refresh": menu_utils.simple_click("refreshButton"),
    "[host | load] (farm | game) <positive_index>": df_utils.async_action(load_game, "positive_index"),
    "[go] back": menu_utils.simple_click("backButton"),

}

def load_grammar():
    extras = [rules.num, df_utils.positive_index, df_utils.positive_num]
    defaults = {'positive_num': 1}
    grammar = menu_utils.build_menu_grammar("titleTextInput", mapping, validate_menu, extras=extras, defaults=defaults) 
    grammar.load()
    