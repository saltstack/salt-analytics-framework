# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import asyncio

import pytest

from saf.collect import test
from saf.models import PipelineRunContext


@pytest.mark.asyncio
async def test_count():
    count = 3
    interval = 0.05
    config = test.TestCollectConfig(
        plugin="test",
        interval=interval,
        count=count,
    )
    config._name = "test-test"  # noqa: SLF001
    ctx: PipelineRunContext[test.TestCollectConfig] = PipelineRunContext.construct(config=config)
    events = []
    async for event in test.collect(ctx=ctx):
        events.append(event)
    assert len(events) == count


@pytest.mark.asyncio
async def test_interval():
    loop = asyncio.get_event_loop()
    count = 3
    interval = 0.05
    config = test.TestCollectConfig(
        plugin="test",
        interval=interval,
        count=count,
    )
    config._name = "test-test"  # noqa: SLF001
    ctx: PipelineRunContext[test.TestCollectConfig] = PipelineRunContext.construct(config=config)
    events = []
    start = loop.time()
    async for event in test.collect(ctx=ctx):
        events.append(event)
    assert len(events) == count
    duration = loop.time() - start
    assert duration >= interval * count
