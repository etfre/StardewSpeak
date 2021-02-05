import dragonfly as df
import title_menu, menu_utils, server

async def get_new_game_menu():
    return await title_menu.get_submenu('characterCustomizationMenu')

async def focus_name_box():
    menu = await get_new_game_menu()
    await menu_utils.click_component(menu['nameBoxCC'])


# sleeping = False


# def notify(message):
#     if message == "sleep":
#         print("Sleeping...")
#     elif message == "wake":
#         print("Awake...")


# def load_sleep_wake_grammar(initial_awake: bool):
#     sleep_grammar = df.Grammar("sleep")

#     def sleep(force=False):
#         global sleeping
#         if not sleeping or force:
#             sleeping = True
#             sleep_grammar.set_exclusiveness(True)
#         notify("sleep")

#     def wake(force=False):
#         global sleeping
#         if sleeping or force:
#             sleeping = False
#             sleep_grammar.set_exclusiveness(False)
#         notify("wake")

#     mapping = {
#         "start listening": df.Function(wake)
#         + df.Function(lambda: df.get_engine().start_saving_adaptation_state()),
#         "stop listening": df.Function(
#             lambda: df.get_engine().stop_saving_adaptation_state()
#         )
#         + df.Function(sleep),
#         "halt listening": df.Function(
#             lambda: df.get_engine().stop_saving_adaptation_state()
#         )
#         + df.Function(sleep),
#     }
#     sleep_rule = df.MappingRule(name="sleep_rule", mapping=mapping)
#     sleep_grammar.add_rule(sleep_rule)
#     sleep_noise_rule = df.MappingRule(
#         name="sleep_noise_rule",
#         mapping={"<text>": df.Function(lambda text: False)},
#         extras=[df.Dictation("text")],
#         context=df.FuncContext(lambda: sleeping),
#     )
#     sleep_grammar.add_rule(sleep_noise_rule)
#     sleep_grammar.load()
#     if initial_awake:
#         wake(force=True)
#     else:
#         sleep(force=True)
