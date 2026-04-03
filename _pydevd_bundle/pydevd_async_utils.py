__all__ = ["eval_async_coro"]

import types


def _get_current_loop():
    import asyncio

    try:
        return asyncio.get_running_loop()
    except (RuntimeError, AttributeError):
        return asyncio.new_event_loop()


def _prepare_coro(coro, _locals, _globals):
    if isinstance(coro, types.CodeType):
        return eval(coro, _locals, _globals)

    return coro


def eval_async_coro(coro, _locals, _globals):
    import asyncio

    coro = _prepare_coro(coro, _locals, _globals)
    loop = _get_current_loop()

    if not loop.is_running():
        return loop.run_until_complete(coro)

    current = asyncio.current_task(loop)

    t = loop.create_task(coro)

    try:
        if current is not None:
            asyncio._leave_task(loop, current)

        while not t.done():
            loop._run_once()

        return t.result()
    finally:
        if current is not None:
            asyncio._enter_task(loop, current)
