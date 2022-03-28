import dragonfly as df
import title_menu, menu_utils, server, df_utils, approximate_matching, items, server
from game_menu import game_menu

inventory_wrapper = menu_utils.InventoryMenuWrapper()


def get_inventory_page(menu):
    page = game_menu.get_page_by_name(menu, "skillsPage")
    return page

async def focus_item_dictation(page, text):
    items_on_page = [x[1]["name"] for x in page["currentRecipePage"]]
    best_idx = approximate_matching.do_match(str(text), items_on_page)
    if best_idx:
        cmp = page["currentRecipePage"][best_idx][0]
        await menu_utils.focus_component(cmp)


mapping = {
    "trash can": menu_utils.simple_click("trashCan"),
}

equipment_icons = {
    "boots": {"name": "Boots", "field": "boots"},
    "hat": {"name": "Hat", "field": "hat"},
    "pants": {"name": "Pants", "field": "pants"},
    "left ring | ring one": {"name": "Left Ring", "field": "leftRing"},
    "right ring | ring to": {"name": "Right Ring", "field": "rightRing"},
    "shirt": {"name": "Shirt", "field": "shirt"},
}


def load_grammar():
    extras = [df_utils.positive_index, items.craftable_items_choice, df.Choice("equipment_icons", equipment_icons)]
    grammar = menu_utils.build_menu_grammar(mapping, get_inventory_page, extras=extras)
    grammar.load()
