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

def init_items():
    return (
        Item("Ancient Seeds"),
        Item("Basic Retaining Soil"),
        Item("Basic Fertilizer"),
        Item("Bee House"),
        Item("Bomb"),
        Item("Cask"),
        Item("Charcoal Kiln"),
        Item("Cheese Press"),
        Item("Chest"),
        Item("Crystalarium"),
        Item("Deluxe Fertilizer"),
        Item("Deluxe Retaining Soil"),
        Item("Deluxe Scarecrow"),
        Item("Deluxe Speed-Gro", ["deluxe speed grow"]),
        Item("Drum Block"),
        Item("Explosive Ammo"),
        Item("Fiber Seeds"),
        Item("Flute Block"),
        Item("Furnace"),
        Item("Garden Pot"),
        Item("Gold Bar"),
        Item("Grass Starter"),
        Item("Hardwood Fence"),
        Item("Hyper Speed-Gro", ["hyper speed grow"]),
        Item("Iridium Sprinkler"),
        Item("Iron Bar"),
        Item("Iron Fence"),
        Item("Keg"),
        Item("Lightning Rod"),
        Item("Loom"),
        Item("Mayonnaise Machine"),
        Item("Mega Bomb"),
        Item("Mini-Jukebox", ["mini jukebox"]),
        Item("Oil Maker"),
        Item("Quality Fertilizer"),
        Item("Quality Retaining Soil"),
        Item("Quality Sprinkler"),
        Item("Preserves Jar"),
        Item("Recycling Machine"),
        Item("Scarecrow"),
        Item("Seed Maker"),
        Item("Slime Egg-Press", ["slime egg press"]),
        Item("Slime Incubator"),
        Item("Speed-Gro", ["speed grow"]),
        Item("Sprinkler"),
        Item("Staircase"),
        Item("Stone Fence"),
        Item("Stone Floor"),
        Item("Stone Sign"),
        Item("Tapper"),
        Item("Torch"),
        Item("Tree Fertilizer"),
        Item("Wild Seeds (Fa)", ["fall wild seeds", "wild fall seeds", "wild seeds fall"]),
        Item("Wild Seeds (Sp)", ["spring wild seeds", "wild spring seeds", "wild seeds spring"]),
        Item("Wild Seeds (Su)", ["summer wild seeds", "wild summer seeds", "wild seeds summer"]),
        Item("Wild Seeds (Wi)", ["winter wild seeds", "wild winter seeds", "wild seeds winter"]),
        Item("Worm Bin"),
        Item("Wood Fence"),
        Item("Wood Floor"),
        Item("Wood Sign"),
    )

def item_commands(items):
    commands = {}
    for item in items:
        for cmd in item.commands:
            assert cmd not in commands
            commands[cmd] = item
    return commands

commands = item_commands(init_items())
items_choice = df.Choice("items", commands)
