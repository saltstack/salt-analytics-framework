# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The NOOP forward plugin exists as an implementation example.

It doesn't really do anything to the collected event
"""
from __future__ import annotations

import logging
from typing import Type

from saf.models import CollectedEvent
from saf.models import ForwardConfigBase
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


def get_config_schema() -> Type[ForwardConfigBase]:
    """
    Get the noop plugin configuration schema.
    """
    return ForwardConfigBase


async def forward(
    *,
    ctx: PipelineRunContext[ForwardConfigBase],  # noqa: ARG001
    event: CollectedEvent,
) -> None:
    """
    Method called to forward the event.
    """
    log.debug("Forwarding: %s", event)
