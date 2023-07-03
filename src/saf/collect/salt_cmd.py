# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Collect events from the event bus.
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator
from typing import Dict
from typing import List
from typing import Type

from salt.client import LocalClient

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class SaltCommandConfig(CollectConfigBase):
    """
    Configuration schema for the beacons collect plugin.
    """

    targets: str
    cmd: str
    args: List[str] | None
    kwargs: Dict[str, str] | None
    interval: float = 5
    cache_flag: str | None = None


def get_config_schema() -> Type[SaltCommandConfig]:
    """
    Get the event bus collect plugin configuration schema.
    """
    return SaltCommandConfig


async def collect(*, ctx: PipelineRunContext[SaltCommandConfig]) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect events.
    """
    config = ctx.config
    client = LocalClient(mopts=ctx.salt_config.copy())

    while True:
        ret = client.cmd(config.targets, config.cmd, arg=config.args, kwarg=config.kwargs)
        event = CollectedEvent(data={config._name: ret})  # noqa: SLF001
        log.debug("CollectedEvent: %s", event)
        yield event
        await asyncio.sleep(config.interval)
