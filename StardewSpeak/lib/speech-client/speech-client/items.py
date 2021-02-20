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
        Item("Wood Fence"),
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
