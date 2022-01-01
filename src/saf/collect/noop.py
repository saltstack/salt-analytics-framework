# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The NOOP collect plugin exists as an implementation example.

It doesn't really do anything to the collected event
"""
import asyncio
import logging
from typing import AsyncIterator
from typing import Type

from saf.models import CollectConfigBase
from saf.models import CollectedEvent


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


async def collect(*, config: NoopConfig) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect events.
    """
    ticks = 0
    while True:
        ticks += 1
        event = CollectedEvent(data={"ticks": ticks})
        log.info("CollectedEvent: %s", event)
        yield event
        await asyncio.sleep(config.interval)
