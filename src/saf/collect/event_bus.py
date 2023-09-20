# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Collect events from the event bus.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator
from typing import Set
from typing import Type

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import SaltEvent
from saf.utils import eventbus

log = logging.getLogger(__name__)


class EventBusConfig(CollectConfigBase):
    """
    Configuration schema for the beacons collect plugin.
    """

    tags: Set[str]


def get_config_schema() -> Type[EventBusConfig]:
    """
    Get the event bus collect plugin configuration schema.
    """
    return EventBusConfig


class EventBusCollectedEvent(CollectedEvent):
    """
    A collected event surrounding a SaltEvent.
    """

    salt_event: SaltEvent


async def collect(
    *, ctx: PipelineRunContext[EventBusConfig]
) -> AsyncIterator[EventBusCollectedEvent]:
    """
    Method called to collect events.
    """
    config = ctx.config
    salt_event: SaltEvent
    log.info("The event bus collect plugin is configured to listen to tags: %s", config.tags)
    async for salt_event in eventbus.iter_events(opts=ctx.salt_config.copy(), tags=config.tags):
        yield EventBusCollectedEvent.construct(salt_event=salt_event, data={"tag": salt_event.tag})
