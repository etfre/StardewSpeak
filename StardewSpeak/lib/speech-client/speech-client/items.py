import dragonfly as df
import re

class Item:

    def __init__(self, name: str, commands=None):
        self.name = name
        if commands is None:
            self.commands = self.commands_from_name(name)
        else:
            self.commands = commands

    def commands_from_name(self, name: str):
        # 'Wood Fence' -> ['wood fence']
        return [name.lower()]

craftable_items = (
    Item("Ancient Seeds"),
    Item("Bait"),
    Item("Barbed Hook"),
    Item("Barrel Brazier"),
    Item("Basic Retaining Soil"),
    Item("Basic Fertilizer"),
    Item("Bee House"),
    Item("Bomb"),
    Item("Bone Mill"),
    Item("Brick Floor"),
    Item("Bug Steak"),
    Item("Campfire"),
    Item("Carved Brazier"),
    Item("Cask"),
    Item("Charcoal Kiln"),
    Item("Cheese Press"),
    Item("Cherry Bomb"),
    Item("Chest"),
    Item("Cobblestone Path"),
    Item("Cookout Kit"),
    Item("Cork Bobber"),
    Item("Crab Pot"),
    Item("Crystalarium"),
    Item("Crystal Floor"),
    Item("Crystal Path"),
    Item("Dark Sign"),
    Item("Deluxe Fertilizer"),
    Item("Deluxe Retaining Soil"),
    Item("Deluxe Scarecrow"),
    Item("Deluxe Speed-Gro", ["deluxe speed grow"]),
    Item("Dressed Spinner"),
    Item("Drum Block"),
    Item("Explosive Ammo"),
    Item("Fairy Dust"),
    Item("Farm Computer"),
    Item("Fiber Seeds"),
    Item("Field Snack"),
    Item("Flute Block"),
    Item("Furnace"),
    Item("Garden Pot"),
    Item("Geode Crusher"),
    Item("Glowstone Ring"),
    Item("Gold Bar"),
    Item("Gold Brazier"),
    Item("Grass Starter"),
    Item("Gravel Path"),
    Item("Hardwood Fence"),
    Item("Hopper"),
    Item("Heavy Tapper"),
    Item("Hyper Speed-Gro", ["hyper speed grow"]),
    Item("Iridium Band"),
    Item("Iridium Sprinkler"),
    Item("Iron Bar"),
    Item("Iron Fence"),
    Item("Iron Lamp-post"),
    Item("Jack-O-Lantern", ["jack-o-lantern"]),
    Item("Keg"),
    Item("Life Elixir"),
    Item("Lightning Rod"),
    Item("Loom"),
    Item("Magic Bait"),
    Item("Magnet"),
    Item("Marble Brazier"),
    Item("Mayonnaise Machine"),
    Item("Mega Bomb"),
    Item("Mini-Jukebox", ["mini jukebox"]),
    Item("Mini-Obelisk", ["mini obelisk"]),
    Item("Monster Musk"),
    Item("Oil Maker"),
    Item("Oil Of Garlic"),
    Item("Ostrich Incubator"),
    Item("Quality Bobber"),
    Item("Quality Fertilizer"),
    Item("Quality Retaining Soil"),
    Item("Quality Sprinkler"),
    Item("Preserves Jar"),
    Item("Rain Totem"),
    Item("Recycling Machine"),
    Item("Ring of Yoba"),
    Item("Rustic Plank Floor"),
    Item("Scarecrow"),
    Item("Seed Maker"),
    Item("Skull Brazier"),
    Item("Slime Egg-Press", ["slime egg press"]),
    Item("Slime Incubator"),
    Item("Solar Panel"),
    Item("Speed-Gro", ["speed grow"]),
    Item("Spinner"),
    Item("Sprinkler"),
    Item("Staircase"),
    Item("Stepping Stone Path"),
    Item("Stone Brazier"),
    Item("Stone Chest"),
    Item("Stone Fence"),
    Item("Stone Floor"),
    Item("Stone Walkway Floor"),
    Item("Stone Sign"),
    Item("Straw Floor"),
    Item("Stump Brazier"),
    Item("Sturdy Ring"),
    Item("Tapper"),
    Item("Tea Sapling"),
    Item("Thorns Ring"),
    Item("Torch"),
    Item("Trap Bobber"),
    Item("Treasure Hunter"),
    Item("Tree Fertilizer"),
    Item("Tub o' Flowers", ["tub [of | o] flowers"]),
    Item("Warp Totem Beach", ["warp totem beach", "beach warp totem"]),
    Item("Warp Totem Farm", ["warp totem farm", "farm warp totem"]),
    Item("Warp Totem Island", ["warp totem island", "island warp totem"]),
    Item("Warp Totem Mountains", ["warp totem mountains", "mountains warp totem"]),
    Item("Warrior Ring"),
    Item("Weathered Floor"),
    Item("Wicked Statue"),
    Item("Wild Bait"),
    Item("Wild Seeds (Fa)", ["fall wild seeds", "wild fall seeds", "wild seeds fall"]),
    Item("Wild Seeds (Sp)", ["spring wild seeds", "wild spring seeds", "wild seeds spring"]),
    Item("Wild Seeds (Su)", ["summer wild seeds", "wild summer seeds", "wild seeds summer"]),
    Item("Wild Seeds (Wi)", ["winter wild seeds", "wild winter seeds", "wild seeds winter"]),
    Item("Worm Bin"),
    Item("Wood Fence"),
    Item("Wood Floor"),
    Item("Wood Lamp-post"),
    Item("Wood Path"),
    Item("Wood Sign"),
    Item("Wooden Brazier"),
)

tools = ()

other_items = (
    Item("Banana Slug"),
    Item("Baseball Bat"),
)

def item_commands(items):
    commands = {}
    for item in items:
        for cmd in item.commands:
            assert cmd not in commands
            commands[cmd] = item
    return commands

craftable_commands = item_commands(craftable_items)
other_item_commands = item_commands(other_items)
craftable_items_choice = df.Choice("craftable_items", craftable_commands)
items_choice = df.Choice("items", {**craftable_commands, **other_item_commands})
