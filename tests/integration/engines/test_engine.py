# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import time

import pytest
from saltfactories.daemons.master import SaltMaster
from saltfactories.daemons.minion import SaltMinion
from saltfactories.utils import random_string


@pytest.fixture(scope="module", autouse=True)
def minion(master: SaltMaster, analytics_events_dump_directory) -> SaltMinion:
    default_config = {
        "engines": ["analytics"],
    }
    factory = master.salt_minion_daemon(random_string("minion-"), defaults=default_config)
    analytics_config = """
    collectors:
      noop-collector:
        plugin: noop
        interval: 1

    processors:
      noop-processor:
        plugin: noop


    forwarders:
      disk-forwarder:
        plugin: disk
        path: {}


    pipelines:
      my-pipeline:
        collect: noop-collector
        process: noop-processor
        forward: disk-forwarder
    """.format(
        analytics_events_dump_directory
    )
    with pytest.helpers.temp_file(
        "analytics", contents=analytics_config, directory=factory.config_dir
    ):
        with factory.started():
            yield factory


def test_events_dumped_to_disk(analytics_events_dump_directory):
    timeout = 10
    while timeout:
        time.sleep(1)
        timeout -= 1
        if len(list(analytics_events_dump_directory.iterdir())) > 3:
            break
    else:
        pytest.fail(f"Failed to find dumped events in {analytics_events_dump_directory}")
