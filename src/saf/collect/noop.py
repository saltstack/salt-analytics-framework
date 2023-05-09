# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The NOOP collect plugin exists as an implementation example.

It doesn't really do anything to the collected event
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator
from typing import Type

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class NoopConfig(CollectConfigBase):
    """
    Configuration schema for the noop collect plugin.
    """

    interval: float = 1


def get_config_schema() -> Type[NoopConfig]:
    """
    Get the noop plugin configuration schema.
    """
    return NoopConfig


async def collect(*, ctx: PipelineRunContext[NoopConfig]) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect events.
    """
    config = ctx.config
    ticks = 0
    while True:
        ticks += 1
        event = CollectedEvent(data={"ticks": ticks})
        log.info("CollectedEvent: %s", event)
        yield event
        await asyncio.sleep(config.interval)
