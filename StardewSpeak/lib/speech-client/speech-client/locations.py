import re

class Location:

    def __init__(self, name: str, commands=None, possessive=False):
        self.name = name
        self.commands = self.format_name(name) if commands is None else commands
        self.possessive = possessive

    def format_name(self, s: str):
        capitals_split = re.findall('[A-Z][a-z]*', s)
        return [x.lower() for x in capitals_split]

def init_locations():
    return (
        Location("AdventureGuild"),
        Location("Backwoods"),
        Location("Beach"),
        Location("Blacksmith"),
        Location("BusStop", ["bus stop"]),
        Location("ElliotHouse", ["elliot's house"], possessive=True),
        Location("Farm"),
        Location("FarmCave", ["farm cave"]),
        Location("FarmHouse", ["farm house"]),
        Location("FishShop"),
        Location("Forest"),
        Location("HaleyHouse", ["haley's house"], possessive=True),
        Location("Hospital"),
        Location("Mountain"),
        Location("JoshHouse", ["josh's house"], possessive=True),
        Location("LeahHouse", ["leah's house"], possessive=True),
        Location("ManorHouse", ["manor house", "[mayor] lewis' house"]),
        Location("Mine", ["mine", "mines"]),
        Location("Mountain"),
        Location("SamHouse", ["sam's house"], possessive=True),
        Location("Saloon", ["[stardrop] saloon"]),
        Location("ScienceHouse"),
        Location("SeedShop", ["[the] seed shop", "pierre's [general] shop", "[pierre's] general shop"], possessive=True),
        Location("Town"),
        Location("Trailer"),
        Location("Woods"),
    )

def location_commands(locs):
    commands = {}
    for loc in locs:
        for cmd in loc.commands:
            assert cmd not in commands
            if not loc.possessive:
                cmd = f'[the] {cmd}'
            commands[cmd] = loc
    return commands

locations = init_locations()