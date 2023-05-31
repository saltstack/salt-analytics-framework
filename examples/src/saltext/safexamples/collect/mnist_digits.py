# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
A plugin which downloads (if not already downloaded) and yields the mnist digits dataset.
"""
from __future__ import annotations

import asyncio
import logging
import pathlib
import random
from typing import AsyncIterator
from typing import Type

from tensorflow import keras

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class MNISTDigitsConfig(CollectConfigBase):
    """
    Configuration schema for the mnist_digits collect plugin.
    """

    path: str
    interval: float = 5


def get_config_schema() -> Type[MNISTDigitsConfig]:
    """
    Get the mnist_digits plugin configuration schema.
    """
    return MNISTDigitsConfig


async def collect(*, ctx: PipelineRunContext[MNISTDigitsConfig]) -> AsyncIterator[CollectedEvent]:
    """
    Periodically yield a random MNIST test digit and it's desired output.
    """
    file_path = pathlib.Path(ctx.config.path)
    log.debug("Downloading the MNIST digits dataset to %s", file_path)
    (x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data(path=file_path)
    x_test = x_test / 255  # Normalize
    x_test_flattened = x_test.reshape(len(x_test), 28 * 28)  # Flatten

    while True:
        idx = random.choice(range(len(x_test_flattened)))  # noqa: S311
        event = CollectedEvent(data={"x": x_test_flattened[idx], "y": y_test[idx]})
        yield event
        await asyncio.sleep(ctx.config.interval)
