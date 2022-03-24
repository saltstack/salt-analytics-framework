# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Remove a field from a collected event
"""
import logging
from typing import Type

from saf.models import CollectedEvent
from saf.models import ProcessConfigBase


log = logging.getLogger(__name__)


class DataRemoveConfig(ProcessConfigBase):
    """
    Configuration schema for the data remove processor plugin.
    """
    field_name: str = "data"


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the data remove processor plugin configuration schema.
    """
    return DataRemoveConfig


async def process(  # pylint: disable=unused-argument
*,
    config: DataRemoveConfig,
    event: CollectedEvent,
) -> CollectedEvent:
    """
    Method called to mask the data based on provided regex rules.
    """
    log.info("Processing event in data_remove: %s", event.json())
    delattr(event, config.field_name)
    return event
