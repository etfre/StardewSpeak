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
		Location("HarveyRoom"),
		Location("SebastianRoom"),
		Location("Tent"),
		Location("WizardHouse"),
		Location("AnimalShop"),
		Location("BusStop"),
		Location("Sewer"),
		Location("BugLand"),
		Location("Desert"),
		Location("Club"),
		Location("SandyHouse"),
		Location("WizardHouseBasement"),
		Location("Railroad"),
		Location("WitchSwamp"),
		Location("WitchHut"),
		Location("WitchWarpCave"),
		Location("Summit"),
		Location("BathHouse_Entry", ["bath house"]),
		Location("BathHouse_MensLocker", ["men's locker"]),
		Location("BathHouse_WomensLocker", ["women's locker"]),
		Location("BathHouse_Pool", ["bath house pool"]),
		Location("CommunityCenter"),
		Location("JojaMart"),
		Location("Greenhouse"),
		Location("SkullCave"),
		Location("Tunnel"),
		Location("Trailer_Big", ["trailer big this is a placeholder"]),
		Location("Cellar", ["cellar one"]),
		Location("Cellar2", ["cellar two"]),
		Location("Cellar3", ["cellar three"]),
		Location("Cellar4", ["cellar four"]),
		Location("BeachNightMarket"),
		Location("MermaidHouse"),
		Location("Submarine"),
		Location("AbandonedJojaMart"),
		Location("MovieTheater"),
		Location("Sunroom"),
		Location("BoatTunnel"),
		Location("IslandSouth"),
		Location("IslandSouthEast"),
		Location("IslandSouthEastCave"),
		Location("IslandEast"),
		Location("IslandWest"),
		Location("IslandNorth"),
		Location("IslandHut"),
		Location("IslandWestCave1"),
		Location("IslandNorthCave1"),
		Location("IslandFieldOffice"),
		Location("IslandFarmHouse"),
		Location("CaptainRoom"),    
		Location("IslandShrine"),
		Location("IslandFarmCave"),
		Location("Caldera"),
		Location("LeoTreeHouse"),
		Location("QiNutRoom"),
        Location("AdventureGuild"),
        Location("Backwoods"),
        Location("Beach"),
        Location("Blacksmith"),
        Location("ElliottHouse", ["elliott's house"]),
        Location("Farm"),
        Location("FarmCave"),
        Location("FarmHouse"),
        Location("FishShop"),
        Location("Forest"),
        Location("HaleyHouse", ["haley's house", "emily's house", "to willow lane"]),
        Location("Hospital"),
        Location("JoshHouse", ["josh's house"]),
        Location("LeahHouse", ["leah's house"]),
        Location("ArchaeologyHouse", ["library museum", "library", "museum", "archaeology house"]),
        Location("ManorHouse", ["manor house", "[mayor] lewis' house"]),
        Location("Mine", ["[the] (mine | mines)"]),
        Location("Mountain"),
        Location("SamHouse", ["sam's house"]),
        Location("Saloon", ["[stardrop] saloon"]),
        Location("ScienceHouse", ["[the] science house", "[the] carpenter's house"]),
        Location("SeedShop", ["[the] seed (shop | store)", "pierre's [general] (shop | store)", "[pierre's] general (shop | store)", "[the] general (shop | store)"]),
        Location("Town"),
        Location("Trailer"),
        Location("Woods"),
    )

async def get_elevator_tiles(item):
    tile = await server.request('GET_ElEVATOR_TILE')
    return [tile]

async def get_ladder_up_tiles(item):
    tile = await server.request('GET_LADDER_UP_TILE')
    return [tile]

points = (
    Point(["go to mail box", "(check | read) mail"], (68, 16), "Farm", pathfind_fn=game.pathfind_to_adjacent, on_arrival=game.do_action),
    Point(["buy backpack"], (7, 19), "SeedShop", facing_direction=constants.NORTH, on_arrival=game.do_action),
    Point(["go to calendar"], (41, 57), "Town", facing_direction=constants.NORTH, on_arrival=game.do_action),
    Point(["go to (billboard | bulletin board)"], (42, 57), "Town", facing_direction=constants.NORTH, on_arrival=game.do_action),
    Point(["go to elevator"], get_elevator_tiles, re.compile(r"UndergroundMine\d+"), facing_direction=constants.NORTH, on_arrival=game.do_action),
    Point(["[go to] ladder up"], get_ladder_up_tiles, re.compile(r"UndergroundMine\d+"), facing_direction=constants.NORTH, on_arrival=game.do_action),
)


def commands(locs):
    import server
    commands = {}
    for loc in locs:
        for cmd in loc.commands:
            if cmd in commands:
                raise ValueError(f"Duplicate location {cmd}")
            commands[cmd] = loc
    return commands


locations = init_locations()