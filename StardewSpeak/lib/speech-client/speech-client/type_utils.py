from typing import TypeVar, Callable, Awaitable, Any

T = TypeVar("T",)
V = TypeVar("V")

AsyncFuncType = Callable[list[T], Awaitable[V]]

async def foo(a: int, b: int) -> str:
    return ""

async def foobar(st: AsyncFuncType):
    return await st(1, 2)

async def _():
    resp = await foobar(foo)