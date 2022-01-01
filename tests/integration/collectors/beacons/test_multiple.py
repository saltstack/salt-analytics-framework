# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import json
import pathlib
import time

import pytest
from saltfactories.daemons.master import SaltMaster
from saltfactories.daemons.minion import SaltMinion
from saltfactories.utils import random_string


@pytest.fixture(scope="module", autouse=True)
def minion(master: SaltMaster, analytics_events_dump_directory) -> SaltMinion:
    default_config = {
        "engines": ["analytics"],
        "beacons": {
            "memusage": [
                {"interval": 0.1},
                {"percent": "0.01%"},
            ],
            "status": [
                {"interval": 0.1},
                {"time": ["all"]},
                {"loadavg": ["all"]},
            ],
        },
    }
    factory = master.salt_minion_daemon(random_string("minion-"), defaults=default_config)
    analytics_config = """
    collectors:
      beacons-collector:
        plugin: beacons
        beacons:
          - "*"

    processors:
      noop-processor:
        plugin: noop


    forwarders:
      disk-forwarder:
        plugin: disk
        path: {}


    pipelines:
      my-pipeline:
        collect: beacons-collector
        process: noop-processor
        forward: disk-forwarder
    """.format(
        analytics_events_dump_directory
    )
    with pytest.helpers.temp_file(
        "analytics", contents=analytics_config, directory=factory.config_dir
    ):
        with factory.started("-l", "trace"):
            yield factory


def test_pipeline(analytics_events_dump_directory: pathlib.Path):
    timeout = 10
    missing_beacons = {"status", "memusage"}
    while timeout:
        if not missing_beacons:
            break
        time.sleep(1)
        timeout -= 1
        for path in analytics_events_dump_directory.iterdir():
            event = json.loads(path.read_text())
            beacon = event["beacon"]
            if beacon in missing_beacons:
                missing_beacons.remove(beacon)
    else:
        pytest.fail(f"Failed to find dumped events in {analytics_events_dump_directory}")
