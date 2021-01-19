import time
import traceback
import weakref
import functools
import queue
import sys
import asyncio
import threading
import uuid
import json
from dragonfly import *
from srabuilder import rules

# from actions import directinput
from srabuilder.actions import directinput
import constants

loop = None
streams = weakref.WeakValueDictionary()
mod_requests = {}


class Stream:
    def __init__(self, name, data=None):
        self.has_value = False
        self.latest_value = None
        self.future = loop.create_future()
        self.name = name
        self.id = f"{name}_{str(uuid.uuid4())}"
        self.closed = False
        self.open(data)

    def set_value(self, value):
        self.latest_value = value
        self.has_value = True
        try:
            self.future.set_result(None)
        except asyncio.InvalidStateError:
            pass

    def open(self, data):
        streams[self.id] = self
        send_message(
            "NEW_STREAM",
            {
                "name": self.name,
                "stream_id": self.id,
                "data": data,
            },
        )

    def close(self):
        if not self.closed:
            self.closed = True
            send_message("STOP_STREAM", self.id)
            del streams[self.id]
            self.set_value(None)

    async def current(self):
        if self.has_value:
            return self.latest_value
        return await self.next()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.close()

    async def next(self):
        if self.closed:
            log("Stream is already closed")
            return
        if not self.future.done():
            await self.future
        if self.closed:
            log(f"Stream {self.name} closed while waiting for next value")
            return
        self.future = loop.create_future()
        return self.latest_value


    async def wait(self, condition):
        item = await self.current()
        while not condition(item):
            item = await self.next()
        return item


def player_status_stream(ticks=1):
    return Stream("UPDATE_TICKED", data={"state": "PLAYER_STATUS", "ticks": ticks})


def on_warped_stream(ticks=1):
    return Stream("ON_WARPED", data={"state": "PLAYER_STATUS", "ticks": ticks})

def on_terrain_feature_list_changed_stream():
    return Stream("ON_TERRAIN_FEATURE_LIST_CHANGED", data={})

def create_stream_next_task(awaitable):
    async def to_call(awaitable):
        try:
            return await awaitable
        except ValueError as e:
            pass

    return loop.create_task(to_call(awaitable))



class AsyncFunction(ActionBase):
    def __init__(self, coro, format_args=None):
        super().__init__()
        self.coro = coro
        self.format_args = format_args

    def execute(self, data=None):
        assert isinstance(data, dict)
        kwargs = {k: v for k, v in data.items() if not k.startswith("_")}
        if self.format_args:
            args = self.format_args(**kwargs)
            return call_soon(self.coro, *args)
        return call_soon(self.coro, **kwargs)

def call_soon(coro, *args, **kw):
    loop.call_soon_threadsafe(_do_create_task, coro, *args, **kw)


def _do_create_task(coro, *args, **kw):
    loop.create_task(coro(*args, **kw))





def setup_async_loop():
    global loop
    loop = asyncio.new_event_loop()
    def async_setup(l):
        l.set_exception_handler(exception_handler)
        l.create_task(async_readline())
        l.create_task(heartbeat(60))
        l.run_forever()

    def exception_handler(loop, context):
        # This only works when there are no references to the above tasks.
        # https://bugs.python.org/issue39256y'
        get_engine().disconnect()
        raise context["exception"]

    async_thread = threading.Thread(target=async_setup, daemon=True, args=(loop,))
    async_thread.start()


async def heartbeat(timeout):
    while True:
        fut = request("HEARTBEAT")
        try:
            resp = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError as e:
            raise e
        await asyncio.sleep(timeout)


async def async_readline():
    # Is there a better way to read async stdin on Windows?
    q = queue.Queue()

    def _run(future_queue):
        while True:
            fut = future_queue.get()
            line = sys.stdin.readline()
            loop.call_soon_threadsafe(fut.set_result, line)

    threading.Thread(target=_run, daemon=True, args=(q,)).start()
    while True:
        fut = loop.create_future()
        q.put(fut)
        line = await fut
        on_message(line)


def request(msg_type, msg=None):
    sent_msg = send_message(msg_type, msg)
    fut = loop.create_future()
    mod_requests[sent_msg["id"]] = fut
    return fut


def send_message(msg_type, msg=None):
    msg_id = str(uuid.uuid4())
    full_msg = {"type": msg_type, "id": msg_id, "data": msg}
    print(json.dumps(full_msg), flush=True)
    return full_msg


def on_message(msg_str):
    try:
        msg = json.loads(msg_str)
    except json.JSONDecodeError:
        raise RuntimeError(f"Got invalid message from mod {msg_str}")
    msg_type = msg["type"]
    msg_data = msg["data"]
    if msg_type == "RESPONSE":
        fut = mod_requests.pop(msg_data["id"], None)
        if fut:
            resp_value = msg_data["value"]
            fut.set_result(resp_value)
    elif msg_type == "STREAM_MESSAGE":
        stream_id = msg_data["stream_id"]
        stream = streams.get(stream_id)
        if stream is None:
            log(f"Can't find {stream_id}")
            send_message("STOP_STREAM", stream_id)
            return
        stream.set_value(msg_data["value"])
        stream.latest_value = msg_data["value"]
        try:
            stream.future.set_result(None)
        except asyncio.InvalidStateError:
            pass
    elif msg_type == "ON_EVENT":
        handle_event(msg_data["eventType"], msg_data["data"])
    else:
        raise RuntimeError(f"Unhandled message type from mod: {msg_type}")


def handle_event(event_type, data):
    if event_type == "ON_WARPED":
        game_state.last_warp = data


def log(msg):
    to_send = msg if isinstance(msg, str) else json.dumps(msg)
    return send_message("LOG", to_send)

async def sleep_forever():
    while True:
        await asyncio.sleep(3600)
