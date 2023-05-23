# Copyright 2022-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import logging
import pprint

import pytest

log = logging.getLogger(__name__)


@pytest.fixture
def process_child_events_count():
    return 3


@pytest.fixture
def processors_config(process_child_events_count):
    return {
        "stage-1": {
            "plugin": "test",
            "delay_range": {
                "minimum": 0.01,
                "maximum": 0.07,
            },
            "child_events_count": process_child_events_count,
        },
        "stage-2": {
            "plugin": "test",
            "delay_range": {
                "minimum": 0.01,
                "maximum": 0.07,
            },
            "child_events_count": process_child_events_count,
        },
    }


@pytest.mark.asyncio
async def test_pipeline(pipeline, collect_events_count, process_child_events_count):
    # Expected Count:
    #  * We generate 3 events
    #  * Each of those events, generates 3 more events - Stage 1
    #  * Each of those events, generates 3 more events - Stage 2
    expected_count = 3 * (5 * process_child_events_count + 1)
    assert "collected_events" not in pipeline.shared_cache
    # run the pipeline
    with pipeline:
        await pipeline.run()
        assert pipeline.shared_cache
        log.debug(
            "Collected Events:\n%s", pprint.pformat(pipeline.shared_cache["collected_events"])
        )
        log.debug(
            "Collected Events Datas:\n%s",
            pprint.pformat(
                [evt.data for evt in pipeline.shared_cache["collected_events"]], width=200
            ),
        )
        forwarded_events_count = len(pipeline.shared_cache["collected_events"])
        assert forwarded_events_count == expected_count
