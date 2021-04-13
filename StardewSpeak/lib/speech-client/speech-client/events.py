import constants
import server
import inspect

def on_key_pressed(data):
    import game
    if data['button'] in game.cardinal_buttons:
        direction = game.buttons_to_directions[data['button']]
        game.set_last_faced_direction(direction)

event_registry = {
    "KEY_PRESSED": on_key_pressed
}

def handle_event(evt):
    handler = event_registry.get(evt['eventType'])
    assert handler
    if handler:
        if inspect.iscoroutinefunction(handler):
            server.call_soon(handler, evt['data'])
        else:
            handler(evt['data'])
