import asyncio
import dragonfly as df
import title_menu, menu_utils, server, df_utils, game, letters, items, server
from game_menu import game_menu

async def get_crafting_page():
    return await menu_utils.get_active_menu('gameMenu')

async def focus_item(item):
    menu = await game_menu.get_game_menu()
    page = game_menu.get_page_by_name(menu, 'craftingPage')
    current_crafting_page = page['pagesOfCraftingRecipes'][page['currentCraftingPageIndex']]
    for cmp, serialized_item in current_crafting_page:
        if item.name == serialized_item['name']:
            await menu_utils.focus_component(cmp)
            return

mapping = {
    "<craftable_items>": df_utils.async_action(focus_item, 'craftable_items'),
}

@menu_utils.valid_menu_test
def is_active():
    menu = game.get_context_menu('gameMenu')
    game_menu.get_page_by_name(menu, 'craftingPage')

def load_grammar():
    grammar = df.Grammar("crafting_page")
    main_rule = df.MappingRule(
        name="crafting_page_rule",
        mapping=mapping,
        extras=[
            df_utils.positive_num,
            items.craftable_items_choice,
        ],
        defaults={'positive_num': 1},
        context=is_active,
    )
    grammar.add_rule(main_rule)
    grammar.load()
