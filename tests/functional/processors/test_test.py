# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.process import test


@pytest.mark.asyncio
async def test_no_child_events():
    initial_event = CollectedEvent(data={"count": 1})
    config = test.TestProcessConfig(
        plugin="test",
    )
    config._name = "test-process"  # noqa: SLF001
    ctx: PipelineRunContext[test.TestProcessConfig] = PipelineRunContext(config=config)
    events = []
    async for event in test.process(ctx=ctx, event=initial_event):
        events.append(event)
    assert len(events) == 1


@pytest.mark.asyncio
async def test_child_events_count():
    count = 3
    initial_event = CollectedEvent(data={"count": 1})
    config = test.TestProcessConfig(
        plugin="test",
        child_events_count=count,
    )
    config._name = "test-process"  # noqa: SLF001
    ctx: PipelineRunContext[test.TestProcessConfig] = PipelineRunContext(config=config)
    events = []
    async for event in test.process(ctx=ctx, event=initial_event):
        events.append(event)
    assert len(events) == count + 1
