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


pytestmark = [pytest.mark.skip_on_windows]


@pytest.fixture(scope="module")
def analytics_config_contents(analytics_events_dump_directory) -> str:
    return """
    collectors:
      mnist-digits-collector:
        interval: 0.1
        plugin: mnist_digits
        path: {}

    processors:
      mnist-network-processor:
        plugin: mnist_network
        model: {}

    forwarders:
      disk-forwarder:
        plugin: disk
        path: {}
        filename: mnist-network-dump
        pretty_print: False

    pipelines:
      my-pipeline:
        collect: mnist-digits-collector
        process: mnist-network-processor
        forward: disk-forwarder
    """.format(
        analytics_events_dump_directory / "mnist_digits",
        pathlib.Path(__file__).resolve().parent / "files" / "mnist",
        analytics_events_dump_directory,
    )


def test_pipeline(analytics_events_dump_directory: pathlib.Path):
    """
    Test output of the MNIST digits network being dumped to disk.
    """
    timeout = 300
    dumpfile = analytics_events_dump_directory / "mnist-network-dump"

    while timeout:
        time.sleep(1)
        timeout -= 1
        if dumpfile.exists() and dumpfile.read_text().strip():
            break
    else:
        pytest.fail(f"Failed to find dumped events in {analytics_events_dump_directory}")

    contents = [
        CollectedEvent.parse_obj(json.loads(i)) for i in dumpfile.read_text().strip().split("\n")
    ]
    for event in contents:
        assert "evaluation" in event.data
        assert "accuracy" in event.data
        assert "loss" in event.data
