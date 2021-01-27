class Location:

    def __init__(self, name: str, commands=None, possessive=False):
        self.name = name
        self.commands = [self.name.lower()] if commands is None else commands
        self.possessive = possessive

def init_locations():
    return (
        Location("Backwoods"),
        Location("BusStop", ["bus stop"]),
        Location("Farm"),
        Location("FarmHouse", ["farm house"]),
        Location("Forest"),
        Location("HaleyHouse", ["haley's house"], possessive=True),
        Location("JoshHouse", ["josh's house"], possessive=True),
        Location("LeahHouse", ["leah's house"], possessive=True),
        Location("Mine", ["mine", "mines"]),
        Location("Mountain"),
        Location("SamHouse", ["sam's house"], possessive=True),
        Location("Town"),
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