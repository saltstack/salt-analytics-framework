# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Run a jupyter notebook using papermill.
"""
from __future__ import annotations

import logging
import pathlib  # noqa: TCH003
from typing import Any
from typing import AsyncIterator
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

import papermill

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

log = logging.getLogger(__name__)


class JupyterNotebookConfig(ProcessConfigBase):
    """
    Configuration schema for the jupyter notebook processor plugin.
    """

    notebook: pathlib.Path
    output_notebook: Optional[pathlib.Path]
    params: Dict[str, Any] = {}
    papermill_kwargs: Dict[str, Any] = {}
    output_tag: Optional[str]
    input_keys: List[str]


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the jupyter notebook processor plugin configuration schema.
    """
    return JupyterNotebookConfig


async def process(
    *,
    ctx: PipelineRunContext[JupyterNotebookConfig],
    event: CollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Run the jupyter notebook, doing papermill parameterizing using the event data given.
    """
    output = ctx.config.output_notebook or ctx.config.notebook
    params = ctx.config.params.copy()
    for key in ctx.config.input_keys:
        params[key] = event.data[key]
    notebook = papermill.execute_notebook(
        str(ctx.config.notebook),
        str(output),
        parameters=params,
        **ctx.config.papermill_kwargs,
    )
    # Now let's find the cell with the output
    # If no output tag is given, we resort to the last cell
    cells = notebook.cells
    if ctx.config.output_tag:
        for cell in cells:
            if ctx.config.output_tag in cell.metadata.tags:
                notebook_output = cell.outputs
                break
    else:
        notebook_output = cells[-1].outputs
    trimmed_outputs = []
    for out in notebook_output:
        if out.output_type == "execute_result":
            trimmed_outputs.append(out)
    event.data = {"trimmed_outputs": trimmed_outputs}

    yield event
