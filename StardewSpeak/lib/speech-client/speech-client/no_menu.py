import dragonfly as df
from srabuilder import rules
import title_menu, menu_utils, server, df_utils, game, container_menu, objective, constants



direction_keys = {
    "north": "w",
    "main": "wd",
    "east": "d",
    "floor": "ds",
    "south": "s",
    "air": "as",
    "west": "a",
    "wash": "aw",
}
direction_nums = {
    "north": 0,
    "east": 1,
    "south": 2,
    "west": 3,
}
nums_to_keys = {
    0: "w",
    1: "d",
    2: "s",
    3: "a",
}
directions = {k: k for k in direction_keys}

mouse_directions = {
    "up": "up",
    "right": "right",
    "down": "down",
    "left": "left",
}


mapping = {
    "<direction_keys>": objective.objective_action(objective.HoldKeyObjective, "direction_keys"),
    "<n> <directions>": objective.objective_action(objective.MoveNTilesObjective, "directions", "n"),
    "item <positive_index>": df_utils.async_action(game.equip_item_by_index, 'positive_index'),
    "equip [melee] weapon": df_utils.async_action(game.equip_item, lambda x: x['type'] == constants.MELEE_WEAPON),
}

@menu_utils.valid_menu_test
def is_active():
    return game.get_context_menu() is None

def load_grammar():
    grammar = df.Grammar("no_menu")
    main_rule = df.MappingRule(
        name="no_menu_rule",
        mapping=mapping,
        extras=[
            rules.num,
            df_utils.positive_index,
            df_utils.positive_num,
            df.Choice("direction_keys", direction_keys),
            df.Choice("direction_nums", direction_nums),
            df.Choice("directions", directions),
        ],
        context=is_active,
        defaults={'positive_num': 1},
    )
    grammar.add_rule(main_rule)
    grammar.load()
    