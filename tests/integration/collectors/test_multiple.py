# Copyright 2022-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import pathlib

import pytest


@pytest.fixture
def collectors_config():
    return {
        "test-collector-1": {
            "plugin": "test",
            "count": 3,
            "interval": 0.05,
        },
        "test-collector-2": {
            "plugin": "test",
            "count": 3,
            "interval": 0.05,
        },
    }


@pytest.mark.asyncio
async def test_pipeline(pipeline, forwarded_events_path: pathlib.Path):
    # run the pipeline
    await pipeline.run()
    assert forwarded_events_path.is_dir()
    forwarded_events_count = len(list(forwarded_events_path.iterdir()))
    assert forwarded_events_count == 6
