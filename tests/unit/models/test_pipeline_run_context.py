# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest
import salt.config
import salt.version

from saf.models import AnalyticsConfig
from saf.models import PipelineRunContext
from saf.pipeline import Pipeline


@pytest.fixture(scope="module", params=["master", "minion"])
def salt_role(request):
    return request.param


@pytest.fixture(scope="module")
def config(salt_role):
    salt_id = "foobar"
    if salt_role == "minion":
        loaded_config = salt.config.minion_config(None, minion_id=salt_id)
    else:
        loaded_config = salt.config.master_config(None)
        loaded_config["id"] = loaded_config["master_id"] = salt_id

    return AnalyticsConfig.model_validate(
        {
            "collectors": {
                "test": {
                    "plugin": "test",
                    "count": 1,
                    "interval": 0.05,
                },
            },
            "processors": {
                "test": {
                    "plugin": "test",
                },
            },
            "forwarders": {
                "test": {
                    "plugin": "test",
                }
            },
            "pipelines": {
                "test": {
                    "collect": "test",
                    "process": "test",
                    "forward": "test",
                }
            },
            "salt_config": loaded_config,
        }
    )


@pytest.fixture(scope="module")
def pipeline(config):
    return Pipeline("test", config.pipelines["test"])


@pytest.fixture(scope="module")
def ctx(pipeline):
    return PipelineRunContext(config=pipeline.collect_configs[0])


def test_info(salt_role, ctx):
    assert ctx.info.salt.id == "foobar"
    assert ctx.info.salt.role == salt_role
    assert ctx.info.salt.version == salt.version.__version__
