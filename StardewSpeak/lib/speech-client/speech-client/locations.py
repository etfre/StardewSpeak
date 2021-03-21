import re
import game, constants, server

class Location:

    def __init__(self, name: str, commands=None):
        self.name = name
        if commands is None:
            self.commands = self.commands_from_name(name)
        else:
            self.commands = commands

    def commands_from_name(self, name: str):
        # 'FarmCave' -> ['farm cave']
        capitals_split = re.findall('[A-Z][a-z]*', name)
        command = ' '.join(capitals_split).lower()
        return [f"[the] {command}"]

class Point:

    def __init__(self, commands, tiles, location, pathfind_fn=game.pathfind_to_tile, facing_direction=None, on_arrival=None):
        self.commands = commands
        if not callable(tiles) and not isinstance(tiles[0], (list, tuple)):
            tiles = [tiles]
        self.tiles = tiles
        self.location = location
        self.pathfind_fn = pathfind_fn
        self.facing_direction = facing_direction
        self.on_arrival = on_arrival

    def commands_from_name(self, name: str):
        # 'FarmCave' -> ['farm cave']
        capitals_split = re.findall('[A-Z][a-z]*', name)
        command = ' '.join(capitals_split).lower()
        return [f"[the] {command}"]

    async def get_tiles(self, item):
        if callable(self.tiles):
            return await self.tiles(item)
        return [{'tileX': x[0], 'tileY': x[1]} for x in self.tiles]

def init_locations():
    return (
        Location("AdventureGuild"),
        Location("Backwoods"),
        Location("Beach"),
        Location("Blacksmith"),
        Location("BusStop"),
        Location("ElliotHouse", ["elliot's house"]),
        Location("Farm"),
        Location("FarmCave"),
        Location("FarmHouse"),
        Location("FishShop"),
        Location("Forest"),
        Location("HaleyHouse", ["haley's house", "emily's house", "to willow lane"]),
        Location("Hospital"),
        Location("JoshHouse", ["josh's house"]),
        Location("LeahHouse", ["leah's house"]),
        Location("LibraryMuseum", ["library museum", "library", "museum"]),
        Location("ManorHouse", ["manor house", "[mayor] lewis' house"]),
        Location("Mine", ["mine", "mines"]),
        Location("Mountain"),
        Location("SamHouse", ["sam's house"]),
        Location("Saloon", ["[stardrop] saloon"]),
        Location("ScienceHouse", ["[the] science house", "[the] carpenter's house"]),
        Location("SeedShop", ["[the] seed (shop | store)", "pierre's [general] (shop | store)", "[pierre's] general (shop | store)", "[the] general (shop | store)"]),
        Location("Town"),
        Location("Trailer"),
        Location("Woods"),
    )


points = (
    Point(["go to mail box", "(check | read) mail"], (68, 16), "Farm", pathfind_fn=game.pathfind_to_adjacent, on_arrival=game.do_action),
    Point(["buy backpack"], (7, 19), "SeedShop", facing_direction=constants.NORTH, on_arrival=game.do_action),
    Point(["buy seeds"], (4, 19), "SeedShop", facing_direction=constants.NORTH, on_arrival=game.do_action),
    Point(["go to calendar"], (41, 57), "Town", facing_direction=constants.NORTH, on_arrival=game.do_action),
    Point(["go to (billboard | bulletin board)"], (42, 57), "Town", facing_direction=constants.NORTH, on_arrival=game.do_action),
)


def commands(locs):
    import server
    commands = {}
    for loc in locs:
        for cmd in loc.commands:
            assert cmd not in commands
            commands[cmd] = loc
    return commands


locations = init_locations()