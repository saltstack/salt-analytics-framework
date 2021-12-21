# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import json
import pathlib
import shutil
import time

import pytest


@pytest.fixture(scope="module")
def temp_logs_dir(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("logs")
    yield tmp_dir
    shutil.rmtree(tmp_dir)


@pytest.fixture(scope="module")
def log_file(temp_logs_dir):
    # Extracted from https://github.com/logpai/logparser/
    log_content = """
    081109 203615 148 INFO dfs.Data$Node: Node 1 for block blk_38865049064139660 terminating
    081109 203807 222 INFO dfs.Data$Node: Node 0 for block blk_-6952295868487656571 terminating
    081109 204005 35 INFO dfs.FSNamesystem: BLOCK* addStoredBlock: blockMap updated: 10.251.73.220:50010
    081109 204015 308 INFO dfs.Data$Node: Node 2 for block blk_8229193803249955061 terminating
    081109 204106 329 INFO dfs.Data$Node: Node 2 for block blk_-6670958622368987959 terminating
    081109 204132 26 INFO dfs.FSNamesystem: BLOCK* addStoredBlock: blockMap updated: 10.251.43.115:50010
    081109 204324 34 INFO dfs.FSNamesystem: BLOCK* addStoredBlock: blockMap updated: 10.251.203.80:50010
    081109 204453 34 INFO dfs.FSNamesystem: BLOCK* addStoredBlock: blockMap updated: 10.250.11.85:50010
    081109 204525 512 INFO dfs.Data$Node: Node 2 for block blk_572492839287299681 terminating
    """

    test_log_file = temp_logs_dir / "test_log"
    test_log_file.write_text(log_content)

    return test_log_file


@pytest.fixture(scope="module")
def analytics_config_contents(log_file, analytics_events_dump_directory):
    analytics_config = """
    collectors:
      logs-collector:
        plugin: logs
        path: {}
        log_format: '<Date> <Time> <Pid> <Level> <Component>: <Content>'

    processors:
      noop-processor:
        plugin: noop


    forwarders:
      disk-forwarder:
        plugin: disk
        path: {}
        filename: logs_output


    pipelines:
      my-pipeline:
        collect: logs-collector
        process: noop-processor
        forward: disk-forwarder
    """.format(
        log_file, analytics_events_dump_directory
    )

    return analytics_config


def test_pipeline(analytics_events_dump_directory: pathlib.Path):
    test_output_path = analytics_events_dump_directory / "logs_output"
    timeout = 10
    while timeout:
        if test_output_path.exists():
            contents = test_output_path.read_text()
            if contents:
                lines = contents.splitlines()
                event = json.loads(lines[0])
                assert (
                    "081109 203615 148 INFO dfs.Data$Node: Node 1 for block blk_38865049064139660 terminating"
                    in event["data"]["log_line"]
                )
                break
        time.sleep(1)
        timeout -= 1
    else:
        pytest.fail(f"Failed to find correct output in {analytics_events_dump_directory}")
