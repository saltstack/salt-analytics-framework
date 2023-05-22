# Copyright 2022-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import pathlib

import pytest


@pytest.fixture
def collectors_config():
    return {
        "test-collector": {
            "plugin": "test",
            "count": 1,
            "interval": 0.05,
        },
    }


@pytest.fixture
def forwarder_dump_path(tmp_path):
    return tmp_path / "forwarder-dump.txt"


@pytest.fixture
def forwarders_config(forwarder_dump_path):
    return {
        "forwarder-1": {
            "plugin": "test",
            "sleep": 0.5,
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
            "sleep": 0.1,
            "path": forwarder_dump_path,
            "message": "3",
        },
    }


@pytest.mark.asyncio
async def test_pipeline(pipeline, forwarder_dump_path: pathlib.Path):
    # run the pipeline
    await pipeline.run()
    expected_outcome = ["1", "2", "3"]
    lines = forwarder_dump_path.read_text().splitlines()
    assert sorted(lines[:3]) == expected_outcome
