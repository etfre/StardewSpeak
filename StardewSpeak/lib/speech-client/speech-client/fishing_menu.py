import game, server, menu_utils, constants
import dragonfly as df

async def catch_fish():
    await server.request('CATCH_FISH')

async def start_fishing():
    with server.player_status_stream() as stream:
        path = await game.pathfind_to_nearest_water(stream)
        # if not path:
        #     return
        await game.equip_item(constants.FISHING_ROD)
        await cast_fishing_rod()
        await wait_for_nibble()
        # await game.swing_tool()

async def cast_fishing_rod():
    with server.tool_status_stream() as tss, game.press_and_release(constants.TOOL_KEY):
        await tss.wait(lambda t: t['isTimingCast'] and t['castingPower'] > 0.95, timeout=10)

async def wait_for_nibble():
    with server.tool_status_stream() as tss:
        await tss.wait(lambda t: t['isNibbling'])
        game.press_key(constants.TOOL_KEY)
        await tss.wait(lambda t: t['isReeling'], timeout=5)


