import asyncio
import dragonfly as df
from srabuilder import rules
import title_menu, menu_utils, server, df_utils, game, container_menu, objective, constants



directions = {
    "north": "north",
    "east": "east",
    "south": "south",
    "west": "west",
}

async def foobar(direction, n=1):
    menu = await menu_utils.get_active_menu()
    move_from = None
    target_components = []
    for cmp in menu_utils.yield_clickable_components(menu):
        center = cmp['center']
        if cmp['containsMouse']:
            move_from = center
        else:
            target_components.append(center)
    if not target_components:
        return
    if move_from is None:
        move_from = await server.get_mouse_position()
    if direction == 'north':
        direction_index, multiplier = 1, -1
    elif direction == 'east':
        direction_index, multiplier = 0, 1
    elif direction == 'south':
        direction_index, multiplier = 1, 1
    elif direction == 'west':
        direction_index, multiplier = 0, -1
    side_index = 0 if direction_index == 1 else 1
    for i in range(n):
        def sort_fn(x):
            val, target_val = move_from[direction_index], x[direction_index]
            direction_diff = (target_val - val) * multiplier
            side_diff = abs(move_from[side_index] - x[side_index])
            right_direction = 0 if direction_diff > 0 else 1
            return (right_direction, 0.1 * direction_diff + 0.9 * side_diff)
        res = min(target_components, key=sort_fn)
        right_direction = sort_fn(res)[0] == 0
        if not right_direction:
            break
        move_from = res
    x, y = move_from
    await server.set_mouse_position(x, y)

mapping = {
    "[<positive_num>] <directions>": df_utils.async_action(foobar, "directions", "positive_num"),
}

@menu_utils.valid_menu_test
def is_active():
    return game.get_context_menu() is not None

def load_grammar():
    grammar = df.Grammar("any_menu")
    main_rule = df.MappingRule(
        name="any_menu_rule",
        mapping=mapping,
        extras=[
            rules.num,
            df_utils.positive_index,
            df_utils.positive_num,
            df.Choice("directions", directions),
        ],
        context=is_active,
        defaults={'positive_num': 1},
    )
    grammar.add_rule(main_rule)
    grammar.load()
    