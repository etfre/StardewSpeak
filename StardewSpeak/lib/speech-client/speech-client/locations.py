import re
import game, constants

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

    def __init__(self, commands, tile, location, adjacent=False, facing_direction=None, on_arrival=None):
        self.commands = commands
        self.tile = tile
        self.location = location
        self.adjacent = adjacent
        self.facing_direction = facing_direction
        self.on_arrival = on_arrival

    def commands_from_name(self, name: str):
        # 'FarmCave' -> ['farm cave']
        capitals_split = re.findall('[A-Z][a-z]*', name)
        command = ' '.join(capitals_split).lower()
        return [f"[the] {command}"]


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
        Location("ManorHouse", ["manor house", "[mayor] lewis' house"]),
        Location("Mine", ["mine", "mines"]),
        Location("Mountain"),
        Location("SamHouse", ["sam's house"]),
        Location("Saloon", ["[stardrop] saloon"]),
        Location("ScienceHouse"),
        Location("SeedShop", ["[the] seed (shop | store)", "pierre's [general] (shop | store)", "[pierre's] general (shop | store)", "[the] general (shop | store)"]),
        Location("Town"),
        Location("Trailer"),
        Location("Woods"),
    )

points = (
    Point(["go to mail box", "(check | read) mail"], (68, 16), "Farm", adjacent=True, on_arrival=game.do_action),
    Point(["buy backpack"], (7, 19), "SeedShop", facing_direction=constants.NORTH, on_arrival=game.do_action),
    Point(["buy seeds"], (4, 19), "SeedShop", facing_direction=constants.NORTH, on_arrival=game.do_action),
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