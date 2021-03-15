import time
import math
import os
import os.path
import json
import collections
import contextlib
import asyncio
from srabuilder.actions import directinput, pydirectinput
import server, constants, async_timeout

last_faced_east_west = constants.WEST
last_faced_north_south = constants.SOUTH

direction_keys = {
    "north": "w",
    "east": "d",
    "south": "s",
    "west": "a",
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

tool_for_object = {
    constants.STONE: {'name': constants.PICKAXE, 'level': 0},
    constants.TWIG: {'name': constants.AXE, 'level': 0},
    constants.WEEDS: {'name': constants.SCYTHE, 'level': 0},
    constants.BOULDER: {'name': constants.PICKAXE, 'level': 2},
    constants.HOLLOW_LOG: {'name': constants.AXE, 'level': 2},
    constants.STUMP: {'name': constants.AXE, 'level': 1},
    # constants.METEORITE: {'name': constants.AXE, 'level': 3},
}

directions = {k: k for k in direction_keys}

DEBRIS = [constants.WEEDS, constants.TWIG, constants.STONE]

context_variables = {
    'ACTIVE_MENU': None
}

class Path:
    def __init__(self, mod_path, location: str):
        tiles = []
        self.tile_indices = {}
        for i, mod_tile in enumerate(mod_path):
            tile = (mod_tile["X"], mod_tile["Y"])
            tiles.append(tile)
            self.tile_indices[tile] = i
        self.tiles = tuple(tiles)
        self.location = location

    def pop(self):
        self.tiles = self.tiles[:-1]

def distance_between_tiles(t1, t2):
    # pathfinding doesn't move diagonally for simplicity so just sum differences between x and y
    return abs(t1[0] - t2[0]) + abs(t1[1] - t2[1]) 
    
def distance_between_tiles_diagonal(t1, t2):
    x_score = abs(t1[0] - t2[0]) ** 2
    y_score = abs(t1[1] - t2[1]) ** 2
    return math.sqrt(x_score + y_score) 

def score_objects_by_distance(start_tile, current_tile, obj_tile, start_weight=0.25, current_weight=0.75):
    assert start_weight + current_weight == 1
    distance_from_start = distance_between_tiles(start_tile, obj_tile)
    distance_from_current = distance_between_tiles(current_tile, obj_tile)
    return start_weight * distance_from_start  + current_weight * distance_from_current

async def get_trees(location: str):
    trees = await server.request('GET_TREES', {"location": location})
    return trees

async def get_fully_grown_trees_and_stumps(location: str):
    trees = await get_trees(location)
    return [t for t in trees if t['stump'] or (t['growthStage'] >= 5 and not t['tapped'])] 

async def get_hoe_dirt(location: str):
    hoe_dirt = await server.request('GET_HOE_DIRT', {"location": location})
    return hoe_dirt or []

async def get_location_objects(location: str):
    objects = await server.request(constants.GET_LOCATION_OBJECTS, {"location": location})
    return objects or []

async def get_resource_clumps(location: str):
    clumps = await server.request(constants.GET_RESOURCE_CLUMPS, {"location": location})
    return clumps


async def get_resource_clump_pieces(location: str):
    clumps = await get_resource_clumps(location)
    return break_into_pieces(clumps)

def break_into_pieces(items):
    pieces = []
    # break up resource clump like a boulder into one object for each tile
    for item in items:
        start_x, start_y = item['tileX'], item['tileY']
        for x in range(item['width']):
            for y in range(item['height']):
                piece = {**item, 'tileX': start_x + x, 'tileY': start_y + y}
                pieces.append(piece)
    return pieces


async def get_diggable_tiles(test_tiles_set, location: str):
    test_tiles = [{'tileX': x, 'tileY': y} for x, y in test_tiles_set]
    filtered = await server.request('GET_DIGGABLE_TILES', {'tiles': test_tiles})
    return filtered

async def gather_items_on_ground(radius):
    '''
    Wood, coal, sap, stone etc.
    '''
    async with server.player_status_stream() as stream:
        player_status = await stream.next()
        location = player_status['location']
        start_tile = player_status["tileX"], player_status["tileY"]
        tile_blacklist = set([start_tile])
        while True:
            items_to_gather = collections.defaultdict(int)
            debris = await server.request('GET_DEBRIS', {"location": "location"})
            test_tiles_set = set()
            for item in debris:
                within_radius = distance_between_tiles(start_tile, (item['tileX'], item['tileY'])) < radius
                if within_radius:
                    debris_tile = item['tileX'], item['tileY']
                    for tile in get_adjacent_tiles(debris_tile) + [debris_tile]:
                        items_to_gather[tile] += 1
                        if tile not in tile_blacklist:
                            test_tiles_set.add(tile)
            if not test_tiles_set:
                return
            player_status = await stream.next()
            current_tile = player_status["tileX"], player_status["tileY"]
            test_tiles = sort_test_tiles(test_tiles_set, start_tile, current_tile, items_to_gather)
            path, invalid = await pathfind_to_resource(test_tiles, location, stream, cutoff=250)
            if path is None:
                server.log(f'Unable to gather {len(test_tiles)} in radius {radius}')
                return
            for tile in path.tiles:
                tile_blacklist.add(tile)
            for tile in invalid:
                tile_blacklist.add(tile)

def sort_test_tiles(tiles, start_tile, current_tile, items_to_gather):
    sorted_tiles = []
    # get maxes for weighted average
    max_start_distance = -1
    max_current_distance = -1
    max_resources_on_tile = -1
    for tile in tiles:
        max_start_distance = max(max_start_distance, distance_between_tiles(start_tile, tile))
        max_current_distance = max(max_current_distance, distance_between_tiles(current_tile, tile))
        max_resources_on_tile = max(max_resources_on_tile, items_to_gather[tile])

    def score_tile(t):
        start_score = distance_between_tiles(start_tile, t) / max_start_distance
        current_score = distance_between_tiles(current_tile, t) / max_current_distance
        resources_score = items_to_gather[t] / max_resources_on_tile
        return 0.05*start_score + 0.25*current_score + 0.7*resources_score

    return sorted(tiles, key=score_tile)

async def pathfind_to_resource(tiles, location, stream, cutoff=-1):
    path = None
    invalid = []
    for tile in tiles:
        try:
            path_to_take = await path_to_tile(tile[0], tile[1], location, cutoff=cutoff)
            path = await travel_path(path_to_take, stream)
        except NavigationFailed as e:
            invalid.append(tile)
        else:
            break
    return path, invalid

async def move_to_location(location: str, stream: server.Stream):
    await ensure_not_moving(stream)
    route = await request_route(location)
    for i, location in enumerate(route[:-1]):
        next_location = route[i + 1]
        server.log(f"Getting path to next location {next_location}")
        await pathfind_to_next_location(next_location, stream)

async def request_route(location: str):
    route = await server.request("ROUTE", {"toLocation": location})
    if route is None:
        raise NavigationFailed(f"Cannot route to location {location}")
    return route


async def path_to_next_location(next_location: str, status_stream):
    player_status = await status_stream.next()
    location = player_status['location']
    location_connection = await server.request("LOCATION_CONNECTION", {"toLocation": next_location})
    if location_connection is None:
        raise NavigationFailed(f"No connection to location {location}")
    x, y, is_door = location_connection['X'], location_connection['Y'], location_connection['IsDoor']
    if is_door:
        path = await path_to_adjacent(x, y, status_stream)
        door_direction = direction_from_tiles(path.tiles[-1], (x, y))
    else:
        path = await path_to_tile(x, y, location)
        door_direction = None
    if path is None:
        raise NavigationFailed(f"Cannot pathfind to connection to location {location}")
    return path, door_direction


async def path_to_tile(x, y, location, cutoff=-1):
    path = await server.request("path_to_tile", {"x": x, "y": y, "location": location, "cutoff": cutoff})
    if path is None:
        raise NavigationFailed(f"Cannot pathfind to {x}, {y} at location {location}")
    return Path(path, location)

async def path_to_player(x, y, location, cutoff=-1):
    path = await server.request("PATH_TO_PLAYER", {"x": x, "y": y, "location": location, "cutoff": cutoff})
    if path is None:
        raise NavigationFailed(f"Cannot pathfind to player from {x}, {y} at location {location}")
    return Path(reversed(path), location)


async def pathfind_to_next_location(
    next_location: str,
    status_stream: server.Stream,
):
    path, door_direction = await path_to_next_location(next_location, status_stream)
    is_done = False
    while not is_done:
        player_status = await status_stream.next()
        current_location = player_status["location"]
        if current_location != path.location:
            if current_location == next_location:
                break
            raise NavigationFailed(
                f"Unexpected location {current_location}, pathfinding for {path.location}"
            )
        is_done = move_update(path, player_status)
    stop_moving()
    if door_direction is not None:
        await face_direction(door_direction, status_stream, move_cursor=True)
        await do_action()


async def travel_path(path: Path, status_stream: server.Stream):
    target_x, target_y = path.tiles[-1]
    is_done = False
    remaining_attempts = 5
    timeout = len(path.tiles * 3)
    try:
        async with async_timeout.timeout(timeout):
            while not is_done:
                player_status = await status_stream.next()
                current_location = player_status["location"]
                if current_location != path.location:
                    raise NavigationFailed(
                        f"Unexpected location {current_location}, pathfinding for {path.location}"
                    )
                try:
                    is_done = move_update(path, player_status)
                except KeyError as e:
                    if remaining_attempts:
                        path = await path_to_tile(target_x, target_y, path.location)
                        remaining_attempts -= 1
                    else:
                        raise e
    except (Exception, BaseException) as e:
        raise e
    finally:
        stop_moving()
    return path

def get_adjacent_tiles(tile):
    x, y = tile
    return [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]

async def path_to_adjacent(x, y, status_stream: server.Stream, cutoff=-1):
    player_status = await status_stream.next()
    location = player_status['location']
    tiles = await server.request("PATH_TO_PLAYER", {"x": x, "y": y, "location": location, "cutoff": cutoff})
    if tiles is None:
        raise NavigationFailed(f"Cannot pathfind to player from {x}, {y} at location {location}")
    tiles =  tiles if len(tiles) == 1 else reversed(tiles[1:])
    return Path(tiles, location)

async def pathfind_to_adjacent(x, y, status_stream: server.Stream, cutoff=-1):
    path = await path_to_adjacent(x, y, status_stream, cutoff=cutoff)
    await travel_path(path, status_stream)
    if path.tiles[-1] != (x, y):
        direction_to_face = direction_from_tiles(path.tiles[-1], (x, y))
        await face_direction(direction_to_face, status_stream)
    return path
    

def move_update(path, player_status):
    """Return False to continue, True when done"""
    current_tile = player_status["tileX"], player_status["tileY"]
    current_tile_index = path.tile_indices[current_tile]
    try:
        target_tile = path.tiles[current_tile_index + 1]
    except IndexError:
        # Last tile, all done!
        if player_status["isMoving"] and facing_tile_center(player_status):
            return False
        return True
    # if not player_status['canMove']:
    #     raise RuntimeError("Player unable to move")
    direction_to_move = direction_from_tiles(current_tile, target_tile)
    # Rule out not moving, moving in the same direction as next tile, and moving in the opposite direction
    current_direction = player_status["facingDirection"]
    turn_coming = (
        player_status["isMoving"]
        and abs(current_direction - direction_to_move) % 2 == 1
    )
    if turn_coming and facing_tile_center(player_status):
        return False
    start_moving(direction_to_move)


def direction_from_tiles(tile, target_tile):
    x, y = tile
    target_x, target_y, = target_tile
    if x == target_x and y > target_y:
        return constants.NORTH
    elif x < target_x and y == target_y:
        return constants.EAST
    elif x == target_x and y < target_y:
        return constants.SOUTH
    elif x > target_x and y == target_y:
        return constants.WEST
    raise ValueError(f'Could not extract direction from {tile} to {target_tile}')

def direction_from_positions(xy, target_xy):
    x, y = xy
    target_x, target_y = target_xy
    xdiff = target_x - x
    ydiff = target_y - y
    if abs(xdiff) > abs(ydiff):
        return constants.EAST if xdiff > 0 else constants.WEST
    return constants.SOUTH if ydiff > 0 else constants.NORTH

def facing_tile_center(player_status):
    """Keep moving towards center of tile before a turn for smoother pathfinding"""
    tile_size = 64  # TODO: get this info from the mod
    position = player_status["position"]
    tile_x, tile_y = player_status["tileX"], player_status["tileY"]
    # x rounds to the nearest tile, y rounds down unless above (or at?) .75, e.g. (21.68, 17.68) becomes (22, 17) and (21.44, 17.77) becomes (21, 18).
    # Normalize so greater than 0 means right/below the center and less than 0 means left/above
    x, y, = (
        position[0] / tile_size - tile_x,
        position[1] / tile_size - tile_y - 0.25,
    )
    assert -0.5 <= x <= 0.5
    assert -0.5 <= y <= 0.5
    current_direction = player_status["facingDirection"]
    # start turning when at least 45% into the tile
    offset_from_mid = 0.05
    if current_direction == constants.NORTH:
        return y + offset_from_mid <= 0
    if current_direction == constants.EAST:
        return x + offset_from_mid <= 0
    if current_direction == constants.SOUTH:
        return y - offset_from_mid >= 0
    if current_direction == constants.WEST:
        return x - offset_from_mid >= 0
    return False

def press_key(key: str):
    directinput.send([key])

@contextlib.contextmanager
def press_and_release(keys):
    for k in keys:
        directinput.press(k)
    try:
        yield
    except (BaseException, Exception) as e:
        raise e
    finally:
        for k in reversed(keys):
            directinput.release(k)

def start_moving(direction: int):
    key_to_press = nums_to_keys[direction]
    to_release = "wasd".replace(key_to_press, "")
    for key in to_release:
        if key in directinput.HELD:
            directinput.release(key)
    if key_to_press not in directinput.HELD:
        directinput.press(key_to_press)
    set_last_faced_direction(direction)

def set_last_faced_direction(direction: int):
    global last_faced_east_west
    global last_faced_north_south
    if direction in (constants.NORTH, constants.SOUTH):
        last_faced_north_south = direction
    else:
        last_faced_east_west = direction

def stop_moving():
    to_release = "wasd"
    for key in to_release:
        if key in directinput.HELD:
            directinput.release(key)


async def ensure_not_moving(stream: server.Stream):
    stop_moving()
    await stream.wait(lambda status: not status["isMoving"], timeout=2)
    await stream.next()


async def face_direction(direction: int, stream: server.Stream, move_cursor=False):
    await ensure_not_moving(stream)
    await server.request("FACE_DIRECTION", direction)
    set_last_faced_direction(direction)
    if move_cursor:
        player_status = await stream.next()
        current_tile = player_status['tileX'], player_status['tileY']
        target_tile = next_tile(current_tile, direction)
        await set_mouse_position_on_tile(target_tile)
    await stream.wait(lambda s: s["facingDirection"] == direction, timeout=1)

async def equip_item(predicate):
    matched_index = None
    row_size = 12
    with server.player_items_stream(ticks=10) as stream, server.async_timeout.timeout(5):
        while True:
            items_info = await stream.next()
            items = items_info['items']
            for idx, inventory_item in enumerate(items):
                if inventory_item and predicate(inventory_item):
                    matched_index = idx
                    break
            if matched_index is None:
                return False
            else:
                if items_info['currentToolIndex'] == matched_index:
                    return True
                if matched_index >= row_size:
                    directinput.send(['tab'])
                else:
                    return await server.request('EQUIP_ITEM_INDEX', {"index": matched_index})

async def equip_item_by_name(name: str):
    predicate = lambda x: x['netName'] == name
    return await equip_item(predicate)

async def equip_item_by_index(idx: int):
    return await server.request('EQUIP_ITEM_INDEX', {"index": idx})

def closest_item_key(start_tile, current_tile, item, player_status):
    target_tile = item['tileX'], item['tileY']
    return distance_between_tiles(current_tile, target_tile)

def generic_next_item_key(start_tile, current_tile, item, player_status):
    target_tile = item['tileX'], item['tileY']
    score = score_objects_by_distance(start_tile, current_tile, target_tile)
    return score

def next_crop_key(start_tile, current_tile, target_tile, player_status):
    score = score_objects_by_distance(start_tile, current_tile, target_tile)
    if direction_from_tiles(current_tile, target_tile) == player_status['facingDirection']:
        score -= 0.1
    return score

def next_debris_key(start_tile, current_tile, debris_obj, player_status):
    target_tile = debris_obj['tileX'], debris_obj['tileY']
    score = score_objects_by_distance(start_tile, current_tile, target_tile)
    return score


def next_hoe_key(start_tile, current_tile, target_tile, player_status):
    score = score_objects_by_distance(start_tile, current_tile, target_tile)
    return score

async def get_tools():
    tools = {}
    async with server.player_items_stream(ticks=10) as stream:
        items_info = await stream.next()
        items = items_info['items']
        for item in items:
            if item and item['isTool']:
                tools[item['netName']] = item
    return tools

async def swing_tool():
    with server.tool_status_stream(ticks=1) as tss:
        with press_and_release(constants.TOOL_KEY):
            await tss.wait(lambda t: t['inUse'], timeout=10)
        await tss.wait(lambda t: not t['inUse'], timeout=10)

async def do_action():
    directinput.send(constants.ACTION_KEY)

async def modify_tiles(get_items, sort_items=generic_next_item_key, pathfind_fn=pathfind_to_adjacent):
    async with server.player_status_stream() as stream:
        player_status = await stream.next()
        start_tile = player_status["tileX"], player_status["tileY"]
        previous_item_count = -1
        while True:
            player_status = await stream.next()
            current_tile = player_status["tileX"], player_status["tileY"]
            items = await get_items(player_status['location'])
            if not items:
                return
            if previous_item_count == len(items):
                raise RuntimeError('Unable to modify current tile')
            previous_item_count = len(items)
            item_path = None
            for item in sorted(items, key=lambda t: sort_items(start_tile, current_tile, t, player_status)):
                try:
                    item_path = await pathfind_fn(item['tileX'], item['tileY'], stream, cutoff=500)
                except NavigationFailed:
                    pass
                else:
                    item_tile = item['tileX'], item['tileY']
                    await set_mouse_position_on_tile(item_tile)
                    yield item
                    break
            if not item_path:
                return

async def set_mouse_position_on_tile(tile):
    x, y = tile
    await server.request('SET_MOUSE_POSITION_ON_TILE', {'x': x, 'y': y})

def is_debris(obj):
    return obj.get('name') in DEBRIS

def next_tile(current_tile, direction: int):
    x, y = current_tile
    if direction == constants.NORTH:
        return x, y - 1
    if direction == constants.EAST:
        return x + 1, y
    if direction == constants.SOUTH:
        return x, y + 1
    if direction == constants.WEST:
        return x - 1, y

async def chop_tree_and_gather_resources(tree):
    async with server.on_terrain_feature_list_changed_stream() as terrain_stream:
        with press_and_release(constants.TOOL_KEY):
            event = await terrain_stream.next()
    await gather_items_on_ground(10)

async def clear_resource_clump(clump):
    tile_x, tile_y = clump['tileX'], clump['tileY']
    with press_and_release(constants.TOOL_KEY):
        while True:
            clumps = await get_resource_clump_pieces('')
            target = None
            for c in clumps:
                if (tile_x, tile_y) == (c['tileX'], c['tileY']):
                    target = c
                    break
            if not target:
                return
            await asyncio.sleep(0.5)

async def find_npc_by_name(name: str, characters_stream):
    characters = await characters_stream.next()
    for char in characters:
        if char['name'] == name:
            return char
    raise NavigationFailed(f'{name} is not in the current location')

async def find_animal_by_name(name: str, animals_stream):
    animals = await animals_stream.next()
    for animal in animals:
        if animal['name'] == name:
            return animal
    raise NavigationFailed(f'{name} is not in the current location')

async def get_current_tile(stream: server.Stream):
    ps = await stream.next()
    current_tile = ps['tileX'], ps['tileY']
    return current_tile

async def refill_watering_can():
    async with server.player_status_stream() as stream:
        path = await pathfind_to_nearest_water(stream)
        if path is not None:
            await equip_item_by_name(constants.WATERING_CAN)
            await swing_tool()

async def write_game_state():
    objs = await get_location_objects('')
    log(objs, "location_objects.json")
    hdt = await get_hoe_dirt('')
    log(hdt, "hoe_dirt.json")

async def get_ready_crafted(loc):
    objs = await get_location_objects(loc)
    ready_crafted = [x for x in objs if x['readyForHarvest'] and x['type'] == "Crafting"]
    return ready_crafted

async def get_forage_visible_items(loc):
    objs = await get_location_objects(loc)
    items = [x for x in objs if x['canBeGrabbed'] and x['type'] == "Basic" and x['isOnScreen'] and x['isForage']]
    return items

async def get_grabble_visible_objects(loc):
    objs = await get_location_objects(loc)
    filtered_objs = []
    for o in objs:
        if o['canBeGrabbed'] and o['type'] == "Basic" and o['isOnScreen'] and o['category'] != 0:
            filtered_objs.append(o)
    return filtered_objs

async def gather_crafted_items():
    async for item in modify_tiles(get_ready_crafted, generic_next_item_key):
        await do_action()

async def gather_forage_items():
    async for item in modify_tiles(get_forage_visible_items, generic_next_item_key):
        await do_action()

async def gather_objects():
    async for item in modify_tiles(get_grabble_visible_objects, generic_next_item_key):
        await do_action()

async def pathfind_to_nearest_water(stream: server.Stream):
    water_tiles = await server.request('GET_WATER_TILES')
    current_tile = await get_current_tile(stream)
    water_tiles.sort(key=lambda t: distance_between_tiles(current_tile, t))
    for wt in water_tiles:
        try:
            return await pathfind_to_adjacent(wt[0], wt[1], stream)
        except NavigationFailed:
            pass
    raise RuntimeError('Cannot access any water tiles in the current location')

async def move_mouse_in_direction(direction: str, amount: int):
    dx, dy = 0, 0
    smallest_unit = 8
    if direction == 'up':
        dy = -amount
    elif direction == 'right':
        dx = amount
    elif direction == 'down':
        dy = amount
    if direction == 'left':
        dx = -amount
    await server.set_mouse_position_relative(dx * smallest_unit, dy * smallest_unit)

async def on_menu_changed(new_menu):
    await server.stop_everything()

def get_context_menu(menu_type=None):
    import menu_utils
    menu = context_variables['ACTIVE_MENU']
    if menu_type is not None:
        if menu is None:
            raise menu_utils.InvalidMenuOption(f'Expecting {menu_type}, got None')
        if menu['menuType'] != menu_type:
            raise menu_utils.InvalidMenuOption(f"Expecting {menu_type}, got {menu['menuType']}")
    return menu

async def get_location_connections():
    return await server.request('GET_LOCATION_CONNECTIONS')

async def go_inside():
    indoors_connections = [x for x in (await get_location_connections()) if not x['TargetIsOutdoors']]
    if indoors_connections:
        with server.player_status_stream() as pss:
            current_tile = await get_current_tile(pss)
            indoors_connections.sort(key=lambda t: distance_between_tiles(current_tile, (t['X'], t['Y'])))
            await pathfind_to_next_location(indoors_connections[0]['TargetName'], pss)

async def get_animals(animals_stream, player_stream):
    animals, player_status = await asyncio.gather(animals_stream.next(), player_stream.next())
    player_tile = player_status['tileX'], player_status['tileY']
    animals.sort(key=lambda x: distance_between_tiles(player_tile, (x['tileX'], x['tileY'])))
    return animals

async def use_tool_on_animal_by_name(name: str):
    did_use = await server.request('USE_TOOL_ON_ANIMAL_BY_NAME', {'name': name})
    async with server.tool_status_stream() as tss:
        await tss.wait(lambda t: not t['inUse'])
    return did_use

def log(obj, name):
    import __main__
    path = os.path.join(os.path.dirname(__main__.__file__), '..', 'debug', name)
    with open(path, 'w') as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, indent=4)

async def pet_animal_by_name(name: str):
    resp = await server.request("PET_ANIMAL_BY_NAME", {"name": name})

class NavigationFailed(Exception):
    pass

async def move_to_character(get_npc):
    import objective
    npc_tile = None
    pathfind_task_wrapper = None
    tile_error_count = 0
    async with server.player_status_stream() as player_stream:
        while True:
            if pathfind_task_wrapper and pathfind_task_wrapper.done:
                if pathfind_task_wrapper.exception:
                    if tile_error_count < 2:
                        pathfind_coro = pathfind_to_adjacent(npc_tile[0], npc_tile[1], player_stream)
                        pathfind_task_wrapper = objective.active_objective.add_task(pathfind_coro)
                        tile_error_count += 1
                        continue
                    else:
                        raise pathfind_task_wrapper.exception
                break
            npc = await get_npc()
            if npc is None:
                raise NavigationFailed
            next_npc_tile = npc['tileX'], npc['tileY']
            if npc_tile != next_npc_tile:
                tile_error_count = 0
                if pathfind_task_wrapper:
                    await pathfind_task_wrapper.cancel()
                npc_tile = next_npc_tile
                pathfind_coro = pathfind_to_adjacent(npc_tile[0], npc_tile[1], player_stream)
                pathfind_task_wrapper = objective.active_objective.add_task(pathfind_coro)
        npc = await get_npc()
        if npc is None:
            raise NavigationFailed
        npx_x, npc_y = npc['center']
        await server.set_mouse_position(npx_x, npc_y, from_viewport=True)
        return npc
        # await move_directly_to_character(get_character, player_stream, npc_stream)

async def move_directly_to_character(get_character, player_stream, npc_stream):
    while True:
        break

async def pathfind_to_tile(x, y, stream, cutoff=-1):
    status = await stream.next()
    loc = status['location']
    path = await path_to_tile(x, y, loc, cutoff=cutoff)
    await travel_path(path, stream)
    return path

async def move_n_tiles(direction: int, n: int, stream):
    status = await stream.next()
    await ensure_not_moving(stream)
    from_x, from_y = status["tileX"], status["tileY"]
    to_x, to_y = from_x, from_y
    if direction == constants.NORTH:
        to_y -= n
    elif direction == constants.EAST:
        to_x += n
    elif direction == constants.SOUTH:
        to_y += n
    elif direction == constants.WEST:
        to_x -= n
    else:
        raise ValueError(f"Unexpected direction {direction}")
    path = await path_to_tile(to_x, to_y, status['location'])
    await travel_path(path, stream)