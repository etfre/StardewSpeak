import asyncio
from srabuilder.actions import directinput
import server, constants



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
directions = {k: k for k in direction_keys}

class Route:
    def __init__(self, mod_paths):
        self.paths = tuple(Path(p) for p in mod_paths)


class Path:
    def __init__(self, mod_path):
        tiles = []
        self.tile_indices = {}
        for i, mod_tile in enumerate(mod_path):
            tile = (mod_tile["X"], mod_tile["Y"])
            tiles.append(tile)
            self.tile_indices[tile] = i
        self.tiles = tuple(tiles)

def distance_between_tiles(t1, t2):
    # pathfinding doesn't move diagonally for simplicity so just sum differences between x and y
    return abs(t1[0] - t2[0]) + abs(t1[1] - t2[1]) 


def sort_objects_by_distance(start_tile, current_tile, obj_tile, start_weight=0.5, current_weight=0.5):
    assert start_weight + current_weight == 1
    distance_from_start = distance_between_tiles(start_tile, obj_tile)
    distance_from_current = distance_between_tiles(current_tile, obj_tile)
    return start_weight * distance_from_start  + current_weight * distance_from_current



async def get_trees(location: str):
    trees = await server.request('GET_TREES', {"location": location})
    return trees

async def gather_debris(radius):
    async with server.player_status_stream() as stream:
        player_status = await stream.next()
        location = player_status['location']
        start_tile = player_status["tileX"], player_status["tileY"]
        visited_tiles = set([start_tile])
        tiles_moving = True
        while True:
            debris = await server.request('GET_DEBRIS', {"location": "location"})
            debris_in_range = [d for d in debris if distance_between_tiles(start_tile, (d['tileX'], d['tileY'])) < radius]
            if tiles_moving and not any([d['isMoving'] for d in debris_in_range]):
                visited_tiles.clear()
                tiles_moving = False
            player_status = await stream.next()
            current_tile = player_status["tileX"], player_status["tileY"]
            target_debris = []
            for d in debris_in_range:
                debris_tile = d['tileX'], d['tileY']
                if debris_tile not in visited_tiles:
                    target_debris.append(d)
            if not target_debris:
                return
            target_debris.sort(key=lambda d: sort_objects_by_distance(start_tile, current_tile, (d['tileX'], d['tileY'])))
            path = await pathfind_to_resource(target_debris, location, stream)
            if path is None:
                raise RuntimeError(f'Unable to gather {len(target_debris)} in radius {radius}')
            for tile in path.tiles:
                visited_tiles.add(tile)
            server.log(path.tiles)

async def pathfind_to_resource(debris, location, stream):
    for d in debris:
        dtile = d['tileX'], d['tileY']
        try:
            return await pathfind_to_position(dtile, location, stream)
        except RuntimeError as e:
            try:
                return await pathfind_to_adjacent(d['tileX'], d['tileY'], stream)
            except RuntimeError:
                pass

async def request_route(location: str, x: int, y: int):
    route = await server.request("ROUTE", {"toLocation": location})
    if route is None:
        raise RuntimeError(f"Cannot pathfind to {x}, {y} at location {location}")
    return route


async def path_to_warp(location: str):
    path = await server.request("PATH_TO_WARP", {"toLocation": location})
    if path is None:
        raise RuntimeError(f"Cannot pathfind to warp to location {location}")
    return Path(path)


async def path_to_position(x, y, location):
    path = await server.request("PATH_TO_POSITION", {"x": x, "y": y, "location": location})
    if path is None:
        raise RuntimeError(f"Cannot pathfind to {x}, {y} at location {location}")
    return Path(path)


async def pathfind_to_warp(
    path: Path,
    location: str,
    next_location: str,
    status_stream: server.Stream,
):
    is_done = False
    while not is_done:
        player_status = await status_stream.next()
        current_location = player_status["location"]
        if current_location != location:
            if current_location == next_location:
                break
            raise RuntimeError(
                f"Unexpected location {current_location}, pathfinding for {location}"
            )
        is_done = move_along_path(path, player_status)
    stop_moving()


async def pathfind_to_position(
    path: Path,
    location: str,
    status_stream: server.Stream,
):
    if not isinstance(path, Path):
        path = await path_to_position(path[0], path[1], location)
    is_done = False
    while not is_done:
        player_status = await status_stream.next()
        current_location = player_status["location"]
        if current_location != location:
            raise RuntimeError(
                f"Unexpected location {current_location}, pathfinding for {location}"
            )   
        is_done = move_along_path(path, player_status)
    stop_moving()
    return path

async def pathfind_to_adjacent(x, y, status_stream: server.Stream):
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
    await pathfind_to_position(shortest_path, location, status_stream)
    direction_to_face = direction_from_tiles(shortest_path.tiles[-1], (x, y))
    await face_direction(direction_to_face, status_stream)
    return shortest_path
    

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
    if tile[1] - 1 == target_tile[1]:
        return constants.NORTH
    elif tile[0] + 1 == target_tile[0]:
        return constants.EAST
    elif tile[1] + 1 == target_tile[1]:
        return constants.SOUTH
    elif tile[0] - 1 == target_tile[0]:
        return constants.WEST
    else:
        raise RuntimeError(f"Points are incorrect: {tile}, {target_tile}")


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


def start_moving(direction: int):
    key_to_press = nums_to_keys[direction]
    to_release = "wasd".replace(key_to_press, "")
    for key in to_release:
        if key in directinput.HELD:
            directinput.release(key)
    if key_to_press not in directinput.HELD:
        directinput.press(key_to_press)



async def ensure_moving(direction: int, stream: server.Stream):
    player_status = await stream.current()
    if direction != player_status["facingDirection"]:
        await ensure_not_moving(stream)
        player_status = await stream.current()
    if not player_status["isMoving"]:
        key_to_press = nums_to_keys[direction]
        directinput.press(key_to_press)
        await stream.wait(lambda x: x["isMoving"])


def stop_moving():
    to_release = "wasd"
    for key in to_release:
        if key in directinput.HELD:
            directinput.release(key)


async def ensure_not_moving(stream: server.Stream):
    stop_moving()
    await stream.wait(lambda status: not status["isMoving"])


async def face_direction(direction: int, stream: server.Stream):
    await ensure_not_moving(stream)
    await server.request("FACE_DIRECTION", direction)
    await stream.wait(lambda s: s["facingDirection"] == direction)