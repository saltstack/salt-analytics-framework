# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The NOOP process plugins exists as an implementation example.

It doesn't really do anything to the collected event
"""
from __future__ import annotations

import logging
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
    yield event
    if config.child_events_count:
        log.info(
            "Generating %d child events using processor config named %r",
            config.child_events_count,
            config.name,
        )
        counter = 1
        while counter <= config.child_events_count:
            yield CollectedEvent(data=dict(**event.data, child_count=counter))
            counter += 1
        log.info(
            "Finished generating %d events for processor config named %r",
            config.child_events_count,
            config.name,
        )
