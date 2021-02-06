import functools
import dragonfly as df
import server

class AsyncFunction(df.ActionBase):
    def __init__(self, async_fn, format_args=None):
        super().__init__()
        self.async_fn = async_fn
        self.format_args = format_args

    async def to_call(self, *a, **kw):
        import server
        try:
            await self.async_fn(*a, **kw)
        except (Exception, asyncio.CancelledError, asyncio.TimeoutError) as e:
            server.log(traceback.format_exc())

    def execute(self, data=None):
        assert isinstance(data, dict)
        kwargs = {k: v for k, v in data.items() if not k.startswith("_")}
        if self.format_args:
            args = self.format_args(**kwargs)
            return server.call_soon(self.to_call, *args)
        return server.call_soon(self.to_call, **kwargs)

class SyncFunction(df.ActionBase):
    def __init__(self, fn, format_args=None):
        super().__init__()
        self.fn = fn
        self.format_args = format_args

    def execute(self, data=None):
        assert isinstance(data, dict)
        kwargs = {k: v for k, v in data.items() if not k.startswith("_")}
        if self.format_args:
            args = self.format_args(**kwargs)
            return self.fn(*args)
        return self.fn(**kwargs)

def format_args(args, **kw):
    formatted_args = []
    for a in args:
        try:
            formatted_arg = kw.get(a, a)
        except TypeError:
            formatted_arg = a
        formatted_args.append(formatted_arg)
    return formatted_args


def sync_action(fn, *args):
    format_args_fn = functools.partial(format_args, args)
    return SyncFunction(fn, format_args=format_args_fn)

def async_action(async_fn, *args):
    format_args_fn = functools.partial(format_args, args)
    return AsyncFunction(async_fn, format_args=format_args_fn)

