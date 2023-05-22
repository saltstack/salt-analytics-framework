# Copyright 2022-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

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
async def test_pipeline(pipeline):
    assert "collected_events" not in pipeline.shared_cache
    # run the pipeline
    with pipeline:
        await pipeline.run()
        assert pipeline.shared_cache
        forwarded_events_count = len(pipeline.shared_cache["collected_events"])
        assert forwarded_events_count == 6
