import dragonfly as df
import functools
from srabuilder import rules
import title_menu, menu_utils, server, df_utils, game, container_menu, objective, constants, items

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
    obj_getter = functools.partial(get_objects_by_name, item.name)
    await game.navigate_nearest_tile(obj_getter)

async def move_and_face_previous_direction(direction: int, n: int):
    async with server.player_status_stream() as stream:
        ps = await stream.next()
        await game.move_n_tiles(direction, n, stream)
        await game.face_direction(ps['facingDirection'], stream, move_cursor=True)

async def get_shipping_bin_tiles(item):
    tile = await server.request('SHIPPING_BIN_TILE')
    return game.break_into_pieces([tile])

async def go_to_shipping_bin():
    async for item in game.navigate_tiles(get_shipping_bin_tiles):
        await game.do_action()
        break

async def get_bed_tile(item):
    tile = await server.request('BED_TILE')
    return [tile]

async def go_to_bed():
    await game.navigate_nearest_tile(get_bed_tile)

mapping = {
    "<direction_keys>": objective.objective_action(objective.HoldKeyObjective, "direction_keys"),
    "<direction_nums> <n>": objective.objective_action(objective.MoveNTilesObjective, "direction_nums", "n"),
    "item <positive_index>": df_utils.async_action(game.equip_item_by_index, 'positive_index'),
    "equip [melee] weapon": df_utils.async_action(game.equip_item, lambda x: x['type'] == constants.MELEE_WEAPON),
    "nearest <items>": objective.function_objective(go_to_object, 'items'),
    "jump <direction_nums> [<positive_num>]": df_utils.async_action(move_and_face_previous_direction, 'direction_nums', "positive_num"),
    "go to bed": objective.function_objective(go_to_bed),
    "go to shipping bin": objective.function_objective(go_to_shipping_bin),
    "water crops": objective.objective_action(objective.WaterCropsObjective),
    "harvest crops": objective.objective_action(objective.HarvestCropsObjective),
    "[open | read] (journal | quest log)": df_utils.async_action(game.press_key, constants.JOURNAL_BUTTON),

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
            df.Choice("direction_keys", game.direction_keys),
            df.Choice("direction_nums", game.direction_nums),
            items.items_choice,
        ],
        context=is_active,
        defaults={'positive_num': 1},
    )
    grammar.add_rule(main_rule)
    grammar.load()
    