# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import asyncio
from typing import Any
from typing import Dict
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from saf.manager import Manager
from saf.models import AnalyticsConfig


if TYPE_CHECKING:
    try:
        from typing import AsyncGenerator
    except ImportError:
        from typing_extensions import AsyncGenerator

try:
    asyncio_fixture = pytest_asyncio.fixture
except AttributeError:
    # On Py3.6 and older version of the pytest gets installed which does not
    # have the `.fixture` function.
    # Fallback to `pytest.fixture`.
    asyncio_fixture = pytest.fixture


async def _run_manager(manager):
    try:
        await manager.run()
    except asyncio.CancelledError:
        pass
    finally:
        await manager.await_stopped()


@pytest.fixture
def analytics_config(analytics_config_dict: Dict[str, Any]):
    return AnalyticsConfig.parse_obj(analytics_config_dict)


@asyncio_fixture
async def manager(analytics_config: AnalyticsConfig) -> "AsyncGenerator[Manager, None]":
    _manager = Manager(analytics_config)
    loop = asyncio.get_event_loop()
    task = loop.create_task(_run_manager(_manager))
    try:
        yield _manager
    finally:
        if not task.done():
            task.cancel()
        await task
