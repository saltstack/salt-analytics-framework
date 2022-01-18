# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest


@pytest.fixture
def analytics_config_dict(analytics_config_dict):
    analytics_config_dict["pipelines"]["my-pipeline"]["enabled"] = True
    return analytics_config_dict


@pytest.mark.asyncio
async def test_start_disabled_pipeline(manager):
    pipeline = "my-pipeline"
    # Make sure we have pipelines configured
    assert manager.pipelines
    assert pipeline in manager.pipelines
    # Make sure those pipelines are running
    assert manager.pipeline_tasks
    assert pipeline in manager.pipeline_tasks
    result = await manager.start_pipeline("my-pipeline")
    assert result is not None
    assert result == f"Pipeline '{pipeline}' is already running"


@pytest.mark.asyncio
async def test_stop_disabled_pipeline(manager):
    pipeline = "my-pipeline"
    # Make sure we have pipelines configured
    assert manager.pipelines
    assert pipeline in manager.pipelines
    # Make sure those pipelines are running
    assert manager.pipeline_tasks
    assert pipeline in manager.pipeline_tasks
    result = await manager.stop_pipeline("my-pipeline")
    assert result is None
