import dragonfly as df
from srabuilder import rules
import menu_utils, server, df_utils, game, objective, server, constants

ANIMAL_QUERY_MENU = 'animalQueryMenu'

mapping = {
    # "pan <direction_keys>": objective.objective_action(objective.HoldKeyObjective, "direction_keys"), # doesn't currently work    
    "yes": menu_utils.simple_click("yesButton"),
    "ok": menu_utils.simple_click("yesButton", "okButton"),
    "(no | cancel)": menu_utils.simple_click("noButton"),
    "[allow | toggle] (pregnancy | reproduction)": menu_utils.simple_click("allowReproductionButton"),
    "sell": menu_utils.simple_click("sellButton"),
    "(change | move) home [building]": menu_utils.simple_click("moveHomeButton"),
    "(name | rename)": menu_utils.simple_click("textBoxCC"),
}

def load_grammar():
    extras = [df.Choice("direction_keys", game.direction_keys)]
    grammar = menu_utils.build_menu_grammar('animal_query_menu', mapping, ANIMAL_QUERY_MENU, extras=extras)
    grammar.load()
    