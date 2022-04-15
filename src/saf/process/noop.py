# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The NOOP process plugins exists as an implementation example.

It doesn't really do anything to the collected event
"""
from __future__ import annotations

import logging
from typing import Type

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase


log = logging.getLogger(__name__)


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the noop plugin configuration schema.
    """
    return ProcessConfigBase


async def process(  # pylint: disable=unused-argument
    *,
    ctx: PipelineRunContext[ProcessConfigBase],
    event: CollectedEvent,
) -> CollectedEvent:
    """
    Method called to process the event.
    """
    log.info("Processing: %s", event)
    return event
