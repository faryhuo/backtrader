import sys
import asyncio
import inspect
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parent
backend_root_str = str(BACKEND_ROOT)
if backend_root_str not in sys.path:
    sys.path.insert(0, backend_root_str)


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as asyncio-compatible")


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    test_function = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_function):
        return None

    marker = pyfuncitem.get_closest_marker("asyncio")
    if marker is None:
        return None

    signature = inspect.signature(test_function)
    kwargs = {
        name: pyfuncitem.funcargs[name]
        for name in signature.parameters
        if name in pyfuncitem.funcargs
    }

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_function(**kwargs))
    finally:
        loop.close()
        asyncio.set_event_loop(None)
    return True
