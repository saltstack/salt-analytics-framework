# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_start_disabled_pipeline(manager):
    pipeline = "my-pipeline"
    # Make sure we have pipelines configured
    assert manager.pipelines
    assert pipeline in manager.pipelines
    # Make sure none of those pipelines are running
    assert not manager.pipeline_tasks
    result = await manager.start_pipeline("my-pipeline")
    assert result is not None
    assert result == f"Pipeline '{pipeline}' is disabled, skipping start."


@pytest.mark.asyncio
async def test_stop_disabled_pipeline(manager):
    pipeline = "my-pipeline"
    # Make sure we have pipelines configured
    assert manager.pipelines
    assert pipeline in manager.pipelines
    # Make sure none of those pipelines are running
    assert not manager.pipeline_tasks
    result = await manager.stop_pipeline("my-pipeline")
    assert result is not None
    assert result == f"Pipeline '{pipeline}' is not running. Not stopping it."
