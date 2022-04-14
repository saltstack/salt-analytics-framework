# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The NOOP forward plugin exists as an implementation example.

It doesn't really do anything to the collected event
"""
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


async def forward(  # pylint: disable=unused-argument
    *,
    ctx: PipelineRunContext[ForwardConfigBase],
    event: CollectedEvent,
) -> None:
    """
    Method called to forward the event.
    """
    log.info("Forwarding: %s", event)
    assert event
