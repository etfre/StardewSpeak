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
tools = {
    "axe": constants.AXE,
    "fishing (rod | pole)": constants.FISHING_ROD,
    "hoe": constants.HOE,
    "pickaxe": constants.PICKAXE,
    "scythe": constants.SCYTHE,
    "watering can": constants.WATERING_CAN,
    "milk pail": constants.MILK_PAIL,
    "pan": constants.PAN,
    "shears": constants.SHEARS,
    "[melee] weapon": constants.MELEE_WEAPON,
}
mouse_directions = {
    "up": "up",
    "right": "right",
    "down": "down",
    "left": "left",
}

npcs = {
    'abigail': constants.ABIGAIL,
    'alex': constants.ALEX,
    'caroline': constants.CAROLINE,
    'demetrius': constants.DEMETRIUS,
    'elliott': constants.ELLIOTT,
    'emily': constants.EMILY,
    'gus': constants.GUS,
    'haley': constants.HALEY,
    'harvey': constants.HARVEY,
    'jas': constants.JAS,
    'jodi': constants.JODI,
    'kent': constants.KENT,
    'leah': constants.LEAH,
    'lewis': constants.LEWIS,
    'marnie': constants.MARNIE,
    'muh roo': constants.MARU,
    'pam': constants.PAM,
    'penny': constants.PENNY,
    'pierre': constants.PIERRE,
    'robin': constants.ROBIN,
    'sam': constants.SAM,
    'sebastian': constants.SEBASTIAN,
    'shane': constants.SHANE,
    'vincent': constants.VINCENT,
    'willy': constants.WILLY,
}


numrep2 = df.Sequence(
    [df.Choice(None, rules.nonZeroDigitMap), df.Repetition(df.Choice(None, rules.digitMap), min=0, max=10)],
    name="n2",
)
num2 = df.Modifier(numrep2, rules.parse_numrep)


mapping = {
    "<direction_keys>": objective.objective_action(objective.HoldKeyObjective, "direction_keys"),
    "<n> <directions>": objective.objective_action(objective.MoveNTilesObjective, "directions", "n"),
    "item <positive_index>": df_utils.async_action(game.equip_item_by_index, 'positive_index'),
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
    