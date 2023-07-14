# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Save the values using numpy of the data dict to paths associated with their keys.
"""
from __future__ import annotations

import logging
import pathlib  # noqa: TCH003
from typing import AsyncIterator
from typing import Type

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

log = logging.getLogger(__name__)


class NumpySaveKeysConfig(ProcessConfigBase):
    """
    Configuration schema for the numpy save keys processor plugin.
    """

    base_path: pathlib.Path


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the numpy save keys plugin configuration schema.
    """
    return NumpySaveKeysConfig


async def process(
    *,
    ctx: PipelineRunContext[NumpySaveKeysConfig],
    event: CollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Save the keys using numpy.
    """
    import numpy as np

    config = ctx.config
    if not config.base_path.exists():
        config.base_path.mkdir(parents=True)
    new_data = {}
    for key, value in event.data.items():
        key_path = config.base_path / f"{key}.npy"
        key_path.touch()
        with key_path.open("wb"):
            np.save(key_path, value, allow_pickle=False)
        event_key = f"{key}_path"
        new_data[event_key] = str(key_path)
        event.data = new_data

    yield event
