# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest


@pytest.fixture
def analytics_config_dict():
    return {
        "collectors": {
            "noop-collector": {"plugin": "noop", "interval": 1},
        },
        "processors": {
            "noop-processor": {
                "plugin": "noop",
            },
        },
        "forwarders": {
            "noop-forwarder": {
                "plugin": "noop",
            },
        },
        "pipelines": {
            "my-pipeline": {
                "enabled": False,
                "collect": "noop-collector",
                "process": "noop-processor",
                "forward": "noop-forwarder",
            }
        },
        "salt_config": {},
    }
