# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Collect events from the event bus.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from typing import AsyncIterator
from typing import Dict
from typing import List
from typing import Type

from pydantic import Field
from salt.client import LocalClient

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class GrainsConfig(CollectConfigBase):
    """
    Configuration schema for the beacons collect plugin.
    """

    targets: str = Field(default="*")
    grains: List[str]
    interval: float = Field(default=5)


def get_config_schema() -> Type[GrainsConfig]:
    """
    Get the event bus collect plugin configuration schema.
    """
    return GrainsConfig


class GrainsCollectedEvent(CollectedEvent):
    """
    A collected event surrounding a SaltEvent.
    """

    minion: str
    grains: Dict[str, Any]


async def collect(*, ctx: PipelineRunContext[GrainsConfig]) -> AsyncIterator[GrainsCollectedEvent]:
    """
    Method called to collect events.
    """
    config = ctx.config
    client = LocalClient(mopts=ctx.salt_config.copy())

    while True:
        ret = client.cmd(config.targets, "grains.item", arg=config.grains)
        for minion, grains in ret.items():
            if grains:
                event = GrainsCollectedEvent.construct(data=ret, minion=minion, grains=grains)
                yield event
        await asyncio.sleep(config.interval)
