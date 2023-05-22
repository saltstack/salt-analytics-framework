# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Test collect plugin.

The test collect plugin exists as an implementation example and also to be able
to test the salt-analytics-framework
"""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import AsyncIterator
from typing import Type

from pydantic import Field

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class TestCollectConfig(CollectConfigBase):
    """
    Test collector configuration.
    """

    interval: float = Field(0.1, gt=0)
    count: int = Field(sys.maxsize, gt=0, lt=sys.maxsize)


def get_config_schema() -> Type[TestCollectConfig]:
    """
    Get the test collect plugin configuration schema.
    """
    return TestCollectConfig


async def collect(
    *,
    ctx: PipelineRunContext[TestCollectConfig],
) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect events, in this case, generate.
    """
    config = ctx.config
    log.info("Generating test events using collector config named %r", config.name)
    counter = 1
    await asyncio.sleep(config.interval)
    while counter <= config.count:
        yield CollectedEvent(
            data={
                "name": config.name,
                "count": counter,
            }
        )
        await asyncio.sleep(config.interval)
        counter += 1
    log.info(
        "Finished generating %d events for collector config named %r", config.count, config.name
    )
