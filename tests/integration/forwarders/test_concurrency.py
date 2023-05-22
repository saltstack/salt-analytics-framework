# Copyright 2022-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import asyncio
import pathlib

import pytest


@pytest.fixture
def forwarder_dump_path(tmp_path):
    return tmp_path / "forwarder-dump.txt"


@pytest.fixture
def analytics_config_dict(forwarder_dump_path):
    return {
        "collectors": {
            "test-collector": {"plugin": "test", "interval": 0.05, "count": 1},
        },
        "forwarders": {
            "forwarder-1": {
                "plugin": "test",
                "sleep": 0.1,
                "path": forwarder_dump_path,
                "message": "1",
            },
            "forwarder-2": {
                "plugin": "test",
                "sleep": 0.3,
                "path": forwarder_dump_path,
                "message": "2",
            },
            "forwarder-3": {
                "plugin": "test",
                "sleep": 0.5,
                "path": forwarder_dump_path,
                "message": "3",
            },
        },
        "pipelines": {
            "my-pipeline": {
                "enabled": True,
                "collect": "test-collector",
                "forward": [
                    "forwarder-3",
                    "forwarder-2",
                    "forwarder-1",
                ],
            }
        },
        "salt_config": {},
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("manager")
async def test_pipeline(forwarder_dump_path: pathlib.Path):
    expected_outcome = ["1", "2", "3"]
    timeout = 5
    while timeout:
        await asyncio.sleep(1)
        timeout -= 1
        if not forwarder_dump_path.exists():
            continue
        lines = forwarder_dump_path.read_text().splitlines()
        if len(lines) >= 3:
            assert sorted(lines[:3]) == expected_outcome
            break
    else:
        pytest.fail(f"Failed to find dumped events in {forwarder_dump_path}")
