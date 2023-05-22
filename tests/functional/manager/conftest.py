# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from saf.manager import Manager
from saf.models import AnalyticsConfig

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
def analytics_config_dict():
    return {
        "collectors": {
            "test-collector": {"plugin": "test", "interval": 1},
        },
        "processors": {
            "noop-processor": {
                "plugin": "noop",
            },
        },
        "forwarders": {
            "noop-forwarder": {
                "plugin": "noop",
            },
        },
        "pipelines": {
            "my-pipeline": {
                "enabled": False,
                "collect": "test-collector",
                "process": "noop-processor",
                "forward": "noop-forwarder",
            }
        },
        "salt_config": {},
    }


@pytest.fixture
def analytics_config(analytics_config_dict):
    return AnalyticsConfig.parse_obj(analytics_config_dict)


@asyncio_fixture
async def manager(analytics_config):
    _manager = Manager(analytics_config)
    loop = asyncio.get_event_loop()
    task = loop.create_task(_run_manager(_manager))
    try:
        yield _manager
    finally:
        if not task.done():
            task.cancel()
        await task
