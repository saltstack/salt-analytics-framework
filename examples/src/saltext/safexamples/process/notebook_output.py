# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Evaluate the output of a Jupyter notebook.
"""
from __future__ import annotations

import logging
from ast import literal_eval
from typing import AsyncIterator
from typing import Type

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

log = logging.getLogger(__name__)


class NotebookOutputConfig(ProcessConfigBase):
    """
    Configuration schema for the notebook output processor plugin.
    """


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the notebook output processor plugin configuration schema.
    """
    return NotebookOutputConfig


async def process(
    *,
    ctx: PipelineRunContext[NotebookOutputConfig],
    event: CollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Process the notebook output and perform some simple averaging.
    """
    if "mnist_model_evaluations" not in ctx.cache:
        ctx.cache["mnist_model_evaluations"] = []

    evaluate = literal_eval(event.data["trimmed_outputs"][0]["data"]["text/plain"])
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
