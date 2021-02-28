import asyncio
import dragonfly as df
import title_menu, menu_utils, server, df_utils, game, letters, items, server
from game_menu import game_menu

inventory = menu_utils.InventoryMenuWrapper(),

async def get_crafting_page():
    menu = await menu_utils.get_active_menu('gameMenu')
    page = game_menu.get_page_by_name(menu, 'craftingPage')
    return page

async def scroll_up(n):
    page = await get_crafting_page()
    await menu_utils.scroll_up(page, n)

async def scroll_down(n):
    page = await get_crafting_page()
    await menu_utils.scroll_down(page, n)

async def focus_item(item):
    page = await get_crafting_page()
    current_crafting_page = page['pagesOfCraftingRecipes'][page['currentCraftingPageIndex']]
    for cmp, serialized_item in current_crafting_page:
        if item.name == serialized_item['name']:
            await menu_utils.focus_component(cmp)
            return True
    return False

mapping = {
    "<craftable_items>": df_utils.async_action(focus_item, 'craftable_items'),
    "[<positive_num>] scroll up": df_utils.async_action(scroll_up, 'positive_num'),
    "[<positive_num>] scroll down": df_utils.async_action(scroll_down, 'positive_num'),
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