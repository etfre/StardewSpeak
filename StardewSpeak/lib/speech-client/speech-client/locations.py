class Location:

    def __init__(self, name: str, commands=None):
        self.name = name
        self.commands = [self.name.lower()] if commands is None else commands

def init_locations():
    return (
        Location("BusStop", ["bus stop"]),
        Location("Farm"),
        Location("FarmHouse", ["farm house"]),
        Location("LeahHouse", ["leah's house"]),
        Location("Town"),
    )

def location_commands(locs):
    commands = {}
    for loc in locs:
        for cmd in loc.commands:
            assert cmd not in commands
            commands[cmd] = loc
    return commands

locations = init_locations()