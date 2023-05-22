# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import pytest

from saf.models import AnalyticsConfig
from saf.pipeline import Pipeline


@pytest.fixture
def collectors_config():
    return {
        "test-collector": {
            "plugin": "test",
            "count": 3,
            "interval": 0.05,
        },
    }


@pytest.fixture
def processors_config():
    return {
        "test-processor": {
            "plugin": "test",
        },
    }


@pytest.fixture
def forwarders_config():
    return {
        "test-forwarder": {
            "plugin": "test",
            "add_event_to_shared_cache": True,
        },
    }


@pytest.fixture
def pipeline_name():
    return "default-pipeline"


@pytest.fixture
def pipelines_config(collectors_config, processors_config, forwarders_config, pipeline_name):
    return {
        pipeline_name: {
            "collect": list(collectors_config),
            "process": list(processors_config),
            "forward": list(forwarders_config),
            "enabled": True,
            "restart": False,
        },
    }


@pytest.fixture
def analytics_config(
    collectors_config, processors_config, forwarders_config, pipelines_config, pipeline_name
):
    return AnalyticsConfig.parse_obj(
        {
            "collectors": collectors_config,
            "processors": processors_config,
            "forwarders": forwarders_config,
            "pipelines": pipelines_config,
            "salt_config": {},
        }
    )


@pytest.fixture
def pipeline(analytics_config, pipeline_name):
    return Pipeline(pipeline_name, analytics_config.pipelines[pipeline_name])
