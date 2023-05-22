# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import pytest


@pytest.fixture
def pipelines_config(pipelines_config, pipeline_name):
    pipelines_config[pipeline_name]["enabled"] = True
    return pipelines_config


@pytest.mark.asyncio
async def test_start_disabled_pipeline(manager, pipeline_name):
    # Make sure we have pipelines configured
    assert manager.pipelines
    assert pipeline_name in manager.pipelines
    # Make sure those pipelines are running
    assert manager.pipeline_tasks
    assert pipeline_name in manager.pipeline_tasks
    result = await manager.start_pipeline(pipeline_name)
    assert result is not None
    assert result == f"Pipeline '{pipeline_name}' is already running"


@pytest.mark.asyncio
async def test_stop_disabled_pipeline(manager, pipeline_name):
    # Make sure we have pipelines configured
    assert manager.pipelines
    assert pipeline_name in manager.pipelines
    # Make sure those pipelines are running
    assert manager.pipeline_tasks
    assert pipeline_name in manager.pipeline_tasks
    result = await manager.stop_pipeline(pipeline_name)
    assert result is None
