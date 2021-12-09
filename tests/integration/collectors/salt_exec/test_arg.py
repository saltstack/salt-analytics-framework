# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import json
import logging
import pathlib
import time

import pytest
from saltfactories.daemons.master import SaltMaster
from saltfactories.daemons.minion import SaltMinion
from saltfactories.utils import random_string

from saf.models import CollectedEvent


log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def minion(master: SaltMaster, analytics_events_dump_directory) -> SaltMinion:
    default_config = {
        "engines": ["analytics"],
    }
    factory = master.salt_minion_daemon(random_string("minion-"), defaults=default_config)
    analytics_config = """
    collectors:
      salt-collector:
        plugin: salt_exec
        interval: 1
        fn: test.arg
        args:
          - arg1
          - 4
          - []
        kwargs:
          kwarg1: hello
          kwarg2: world


    processors:
      noop-processor:
        plugin: noop


    forwarders:
      disk-forwarder:
        plugin: disk
        filename: salt_exec_arg_dump
        path: {}


    pipelines:
      my-pipeline:
        collect: salt-collector
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


def test_pipeline(minion, analytics_events_dump_directory: pathlib.Path):
    """
    Test output of test.arg being dumped to disk.
    """
    timeout = 10
    dumpfile = analytics_events_dump_directory / "salt_exec_arg_dump"

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
        assert event.data["ret"] == {
            "args": ["arg1", 4, []],
            "kwargs": {"kwarg1": "hello", "kwarg2": "world"},
        }
