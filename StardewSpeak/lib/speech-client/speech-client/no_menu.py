import dragonfly as df
import functools
from srabuilder import rules
import title_menu, menu_utils, server, df_utils, game, container_menu, objective, constants, items



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

async def get_objects_by_name(name: str, loc: str):
    objs = await game.get_location_objects('')
    return [x for x in objs if x['name'] == name] 

async def go_to_object(item: items.Item):
    server.log(item.name)
    obj_getter = functools.partial(get_objects_by_name, item.name)
    async for item in game.modify_tiles(obj_getter, game.closest_item_key):
        await game.do_action()
        return
    raise RuntimeError(f'No {item.name} objects in the current location')

async def move_and_face_previous_direction(direction: int, n: int):
    async with server.player_status_stream() as stream:
        ps = await stream.next()
        await game.move_n_tiles(direction, n, stream)
        await game.face_direction(ps['facingDirection'], stream, move_cursor=True)


mapping = {
    "<direction_keys>": objective.objective_action(objective.HoldKeyObjective, "direction_keys"),
    "<direction_nums> <n>": objective.objective_action(objective.MoveNTilesObjective, "direction_nums", "n"),
    "item <positive_index>": df_utils.async_action(game.equip_item_by_index, 'positive_index'),
    "equip [melee] weapon": df_utils.async_action(game.equip_item, lambda x: x['type'] == constants.MELEE_WEAPON),
    "go to [nearest] <items>": df_utils.async_action(go_to_object, 'items'),
    "jump <direction_nums> [<positive_num>]": df_utils.async_action(move_and_face_previous_direction, 'direction_nums', "positive_num"),
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
            items.items_choice,
        ],
        context=is_active,
        defaults={'positive_num': 1},
    )
    grammar.add_rule(main_rule)
    grammar.load()
    