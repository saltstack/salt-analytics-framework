# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import json
import logging
import pathlib
import time

import pytest

from saf.models import CollectedEvent

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def analytics_config_contents(analytics_events_dump_directory) -> str:
    return """
    collectors:
      salt-collector:
        plugin: salt_exec
        interval: 1
        fn: config.get
        args:
          - id


    processors:
      test-processor:
        plugin: test


    forwarders:
      disk-forwarder:
        plugin: disk
        filename: salt_exec_config_dump
        path: {}


    pipelines:
      my-pipeline:
        collect: salt-collector
        process: test-processor
        forward: disk-forwarder
    """.format(
        analytics_events_dump_directory
    )


def test_pipeline(minion, analytics_events_dump_directory: pathlib.Path):
    """
    Test output of config.get being dumped to disk.
    """
    timeout = 10
    dumpfile = analytics_events_dump_directory / "salt_exec_config_dump"

    while timeout:
        time.sleep(1)
        timeout -= 1
        if dumpfile.exists() and dumpfile.read_text().strip():
            break
    else:
        pytest.fail(f"Failed to find dumped events in {analytics_events_dump_directory}")

    contents = [
        CollectedEvent.model_validate(json.loads(i))
        for i in dumpfile.read_text().strip().split("\n")
    ]
    for event in contents:
        assert event.data["ret"] == minion.id
