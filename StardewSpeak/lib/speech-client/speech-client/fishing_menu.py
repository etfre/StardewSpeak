import game, server, menu_utils, constants
import dragonfly as df

async def catch_fish():
    await server.request('CATCH_FISH')

async def start_fishing():
    with server.player_status_stream() as stream:
        path = await game.pathfind_to_nearest_water(stream)
        await game.equip_item_by_name(constants.FISHING_ROD)
        await cast_fishing_rod()
        await wait_for_nibble()

async def cast_fishing_rod():
    async with server.tool_status_stream() as tss, game.press_and_release(constants.USE_TOOL_BUTTON):
        await tss.wait(lambda t: t['isTimingCast'] and t['castingPower'] > 0.95, timeout=10)

async def wait_for_nibble():
    with server.tool_status_stream() as tss:
        await tss.wait(lambda t: t['isNibbling'])
        game.press_key(constants.USE_TOOL_BUTTON)
        await tss.wait(lambda t: t['isReeling'])


