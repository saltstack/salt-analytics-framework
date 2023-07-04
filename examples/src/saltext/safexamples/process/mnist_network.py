# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Run the salt-analytics-framework port of the MNIST network.
"""
from __future__ import annotations

import logging
import pathlib
from typing import AsyncIterator
from typing import Type

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

log = logging.getLogger(__name__)


class MNISTNetworkConfig(ProcessConfigBase):
    """
    Configuration schema for the MNIST network processor plugin.
    """

    model: str


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the MNIST network processor plugin configuration schema.
    """
    return MNISTNetworkConfig


async def process(
    *,
    ctx: PipelineRunContext[MNISTNetworkConfig],
    event: CollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Run the MNIST network.
    """
    import numpy as np
    from tensorflow import keras

    if "mnist_model" not in ctx.cache:
        model_path = pathlib.Path(ctx.config.model)
        log.debug("Loading the mnist model from %s", model_path)
        ctx.cache["mnist_model"] = keras.models.load_model(model_path)
        ctx.cache["mnist_model_evaluations"] = []
    else:
        log.debug("Did not load the model, already cached it")

    model = ctx.cache["mnist_model"]
    x = event.data["x"]
    y = event.data["y"]
    evaluate = model.evaluate(np.asarray([x]), np.asarray([y]))
    log.debug("Evaluate result: %s", evaluate)
    ctx.cache["mnist_model_evaluations"].append(evaluate)
    avg_accuracy = sum([res[1] for res in ctx.cache["mnist_model_evaluations"]]) / len(
        ctx.cache["mnist_model_evaluations"]
    )
    avg_loss = sum([res[0] for res in ctx.cache["mnist_model_evaluations"]]) / len(
        ctx.cache["mnist_model_evaluations"]
    )
    log.debug("Average accuracy: %s, average loss: %s", avg_accuracy, avg_loss)
    event.data = {
        "evaluation": evaluate,
        "accuracy": avg_accuracy,
        "loss": avg_loss,
    }

    yield event
