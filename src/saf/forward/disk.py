# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The disk forward plugin exists as an implementation example.

It just dumps the collected events to disk
"""
import logging
import pathlib
from typing import Type

from saf.models import CollectedEvent
from saf.models import ForwardConfigBase

log = logging.getLogger(__name__)


class DiskConfig(ForwardConfigBase):
    """
    Configuration schema for the disk forward plugin.
    """

    path: pathlib.Path


def get_config_schema() -> Type[DiskConfig]:
    """
    Get the noop plugin configuration schema.
    """
    return DiskConfig


async def forward(
    *,
    config: DiskConfig,
    event: CollectedEvent,
) -> None:
    """
    Method called to forward the event.
    """
    if not config.path.exists():
        config.path.mkdir(parents=True)
    file_count = len(list(config.path.iterdir()))
    dest = config.path / f"event-dump-{file_count + 1}.json"
    wrote = dest.write_text(event.json())
    log.debug("Wrote %s bytes to %s", wrote, dest)
