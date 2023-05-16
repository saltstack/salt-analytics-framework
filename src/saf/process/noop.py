# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The NOOP process plugins exists as an implementation example.

It doesn't really do anything to the collected event
"""
from __future__ import annotations

import logging
from typing import AsyncIterator
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


async def process(
    *,
    ctx: PipelineRunContext[ProcessConfigBase],  # noqa: ARG001
    event: CollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Method called to process the event.
    """
    log.debug("Processing: %s", event)
    yield event
