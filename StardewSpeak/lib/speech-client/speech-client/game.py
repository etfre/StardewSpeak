import time
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
    constants.STONE: constants.PICKAXE,
    constants.TWIG: constants.AXE,
    constants.WEEDS: constants.SCYTHE,
}

directions = {k: k for k in direction_keys}

DEBRIS = [constants.WEEDS, constants.TWIG, constants.STONE]


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

def distance_between_tiles(t1, t2):
    # pathfinding doesn't move diagonally for simplicity so just sum differences between x and y
    return abs(t1[0] - t2[0]) + abs(t1[1] - t2[1]) 


def score_objects_by_distance(start_tile, current_tile, obj_tile, start_weight=0.25, current_weight=0.75):
    assert start_weight + current_weight == 1
    distance_from_start = distance_between_tiles(start_tile, obj_tile)
    distance_from_current = distance_between_tiles(current_tile, obj_tile)
    return start_weight * distance_from_start  + current_weight * distance_from_current



async def get_trees(location: str):
    trees = await server.request('GET_TREES', {"location": location})
    return trees


async def get_hoe_dirt(location: str):
    hoe_dirt = await server.request('GET_HOE_DIRT', {"location": location})
    return hoe_dirt or []

async def get_location_objects(location: str):
    objects = await server.request(constants.GET_LOCATION_OBJECTS, {"location": location})
    return objects or []

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
                    for tile in adjacent_tiles(debris_tile) + [debris_tile]:
                        items_to_gather[tile] += 1
                        if tile not in tile_blacklist:
                            test_tiles_set.add(tile)
            if not test_tiles_set:
                return
            player_status = await stream.next()
            current_tile = player_status["tileX"], player_status["tileY"]
            test_tiles = sort_test_tiles(test_tiles_set, start_tile, current_tile, items_to_gather)
            path, invalid = await pathfind_to_resource(test_tiles, location, stream)
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

async def pathfind_to_resource(tiles, location, stream):
    path = None
    invalid = []
    for tile in tiles:
        try:
            path_to_take = await path_to_position(tile[0], tile[1], location)
            path = await pathfind_to_position(path_to_take, stream)
        except RuntimeError as e:
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
        raise RuntimeError(f"Cannot route to location {location}")
    return route


async def path_to_next_location(next_location: str, status_stream):
    player_status = await status_stream.next()
    location = player_status['location']
    location_connection = await server.request("LOCATION_CONNECTION", {"toLocation": next_location})
    if location_connection is None:
        raise RuntimeError(f"No connection to location {location}")
    x, y, is_door = location_connection['X'], location_connection['Y'], location_connection['IsDoor']
    if is_door:
        path = await path_to_adjacent(x, y, status_stream)
        door_direction = direction_from_tiles(path.tiles[-1], (x, y))
    else:
        path = await path_to_position(x, y, location)
        door_direction = None
    if path is None:
        raise RuntimeError(f"Cannot pathfind to connection to location {location}")
    return path, door_direction


async def path_to_position(x, y, location):
    path = await server.request("PATH_TO_POSITION", {"x": x, "y": y, "location": location})
    if path is None:
        raise RuntimeError(f"Cannot pathfind to {x}, {y} at location {location}")
    return Path(path, location)


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
            raise RuntimeError(
                f"Unexpected location {current_location}, pathfinding for {path.location}"
            )
        is_done = move_along_path(path, player_status)
    stop_moving()
    if door_direction is not None:
        await face_direction(door_direction, status_stream)
        await do_action()


async def pathfind_to_position(path: Path, status_stream: server.Stream):
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
                    raise RuntimeError(
                        f"Unexpected location {current_location}, pathfinding for {path.location}"
                    )
                try:
                    is_done = move_along_path(path, player_status)
                except KeyError as e:
                    if remaining_attempts:
                        path = await path_to_position(target_x, target_y, path.location)
                        remaining_attempts -= 1
                    else:
                        raise e
    except (Exception, BaseException) as e:
        raise e
    finally:
        stop_moving()
    return path

def adjacent_tiles(tile):
    x, y = tile
    return [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]

async def path_to_adjacent(x, y, status_stream: server.Stream):
    player_status = await status_stream.next()
    location = player_status['location']
    current_tile = player_status["tileX"], player_status["tileY"]
    adjacent_tiles = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
    adjacent_tiles.sort(key=lambda t: distance_between_tiles(current_tile, t))
    potential_paths = {}
    shortest_path = None
    tested_tiles = set()
    for adjacent_tile in adjacent_tiles:
        if adjacent_tile in tested_tiles:
            continue
        tested_tiles.add(adjacent_tile)
        try:
            path = await path_to_position(adjacent_tile[0], adjacent_tile[1], location)
        except RuntimeError:
            continue
        # shortcut if path goes through another adjacent tile
        tile_indices = {}
        for i, tile in enumerate(path.tiles[:-1]):
            tile_indices[tile] = i
            if tile in adjacent_tiles:
                tested_tiles.add(tile)
                path.tiles = path.tiles[:i + 1]
                path.tile_indices = tile_indices
                break
        if shortest_path is None or len(path.tiles) < len(shortest_path.tiles):
            shortest_path = path
            tile_diff = distance_between_tiles(current_tile, shortest_path.tiles[-1])
            if not tile_diff:
                break
            extra_tiles_ratio = len(path.tiles) / tile_diff
            is_efficient = len(path.tiles) <= 8 or extra_tiles_ratio  <= 1.5
            if is_efficient:
                break
    if shortest_path is None:
        raise RuntimeError(f"No path found adjacent to {x}, {y}")
    return shortest_path


async def pathfind_to_adjacent(x, y, status_stream: server.Stream):
    path = await path_to_adjacent(x, y, status_stream)
    await pathfind_to_position(path, status_stream)
    direction_to_face = direction_from_tiles(path.tiles[-1], (x, y))
    await face_direction(direction_to_face, status_stream)
    return path
    

def move_along_path(path, player_status):
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


def facing_tile_center(player_status):
    """Keep moving towards center of tile before a turn for smoother pathfinding"""
    tile_size = 64  # TODO: get this info from the mod
    position = player_status["position"]
    tile_x, tile_y = player_status["tileX"], player_status["tileY"]
    # x rounds to the nearest tile, y rounds down unless above (or at?) .75, e.g. (21.68, 17.68) becomes (22, 17) and (21.44, 17.77) becomes (21, 18).
    # Normalize so greater than 0 means right/below the center and less than 0 means left/above
    x, y, = (
        position["x"] / tile_size - tile_x,
        position["y"] / tile_size - tile_y - 0.25,
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


async def face_direction(direction: int, stream: server.Stream):
    await ensure_not_moving(stream)
    await server.request("FACE_DIRECTION", direction)
    set_last_faced_direction(direction)
    await stream.wait(lambda s: s["facingDirection"] == direction, timeout=1)

async def equip_item(item: str):
    matched_index = None
    row_size = 12
    with server.player_items_stream(ticks=10) as stream, server.async_timeout.timeout(5):
        while True:
            items_info = await stream.next()
            items = items_info['items']
            for idx, inventory_item in enumerate(items):
                if inventory_item and inventory_item['netName'] == item:
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

async def swing_tool():
    with server.tool_status_stream(ticks=1) as tss:
        with press_and_release(constants.TOOL_KEY):
            await tss.wait(lambda t: t['inUse'], timeout=10)
        await tss.wait(lambda t: not t['inUse'], timeout=10)

async def do_action():
    directinput.send(constants.ACTION_KEY)

async def modify_tiles(get_items, sort_items, at_tile):
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
                    item_path = await pathfind_to_adjacent(item['tileX'], item['tileY'], stream)
                except RuntimeError:
                    continue
                else:
                    await at_tile(item)
                    break
            if not item_path:
                return

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
    await gather_items_on_ground(15)

async def find_npc_by_name(name: str, characters_stream):
    characters = await characters_stream.next()
    for char in characters:
        if char['name'] == name:
            return char
    raise RuntimeError(f'{name} is not in the current location')

async def get_current_tile(stream: server.Stream):
    ps = await stream.next()
    current_tile = ps['tileX'], ps['tileY']
    return current_tile

async def refill_watering_can():
    async with server.player_status_stream() as stream:
        path = await pathfind_to_nearest_water(stream)
        if path is not None:
            await equip_item(constants.WATERING_CAN)
            await swing_tool()

async def pathfind_to_nearest_water(stream: server.Stream):
    water_tiles = await server.request('GET_WATER_TILES')
    current_tile = await get_current_tile(stream)
    water_tiles.sort(key=lambda t: distance_between_tiles(current_tile, t))
    for wt in water_tiles:
        try:
            return await pathfind_to_adjacent(wt[0], wt[1], stream)
        except RuntimeError:
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