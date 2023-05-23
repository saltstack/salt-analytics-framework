# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The NOOP process plugins exists as an implementation example.

It doesn't really do anything to the collected event
"""
from __future__ import annotations

import asyncio
import logging
import random
import sys
from typing import AsyncIterator
from typing import Optional
from typing import Type

from pydantic import Field

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

log = logging.getLogger(__name__)


class TestProcessConfig(ProcessConfigBase):
    """
    Test collector configuration.
    """

    delay: Optional[float] = Field(None, gt=0)
    delay_range: Optional[tuple[float, float]] = None
    child_events_count: Optional[int] = Field(None, gt=0, lt=sys.maxsize)


def get_config_schema() -> Type[TestProcessConfig]:
    """
    Get the test collect plugin configuration schema.
    """
    return TestProcessConfig


async def process(
    *,
    ctx: PipelineRunContext[TestProcessConfig],
    event: CollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect events, in this case, generate.
    """
    config = ctx.config
    log.info("Processing event %r using processor config named %r", event, config.name)
    if config.delay:
        await asyncio.sleep(config.delay)
    elif config.delay_range:
        await asyncio.sleep(
            random.uniform(*config.delay_range),  # noqa: S311
        )
    yield event
    if config.child_events_count:
        log.info(
            "Generating %d child events using processor config named %r",
            config.child_events_count,
            config.name,
        )
        counter = 1
        while counter <= config.child_events_count:
            if config.delay:
                await asyncio.sleep(config.delay * (config.child_events_count / counter))
            elif config.delay_range:
                await asyncio.sleep(
                    random.uniform(  # noqa: S311
                        *config.delay_range,
                    )
                    * (config.child_events_count / counter),
                )
            event_data = dict(**event.data)
            event_data[f"{config.name}-child-count"] = counter
            yield CollectedEvent(data=event_data)
            counter += 1
        log.info(
            "Finished generating %d events for processor config named %r",
            config.child_events_count,
            config.name,
        )
