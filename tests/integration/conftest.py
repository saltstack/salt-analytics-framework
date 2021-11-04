# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import shutil
from typing import Iterator

import pytest
from saltfactories.cli.call import SaltCall
from saltfactories.cli.run import SaltRun
from saltfactories.cli.salt import SaltCli
from saltfactories.daemons.master import SaltMaster
from saltfactories.daemons.minion import SaltMinion
from saltfactories.utils import random_string


@pytest.fixture(scope="package")
def analytics_events_dump_directory(tmp_path_factory) -> Iterator[pathlib.Path]:
    dump_path = tmp_path_factory.mktemp("analytics-events-dump")
    try:
        yield dump_path
    finally:
        shutil.rmtree(str(dump_path), ignore_errors=True)


@pytest.fixture(scope="package")
def master(salt_factories, analytics_events_dump_directory) -> SaltMaster:
    default_config = {
        "engines": ["analytics"],
    }
    factory = salt_factories.salt_master_daemon(random_string("master-"), defaults=default_config)
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


@pytest.fixture(scope="package")
def minion(master: SaltMaster) -> SaltMinion:
    factory = master.salt_minion_daemon(random_string("minion-"))
    with factory.started():
        yield factory


@pytest.fixture
def salt_run_cli(master: SaltMaster) -> SaltRun:
    return master.get_salt_run_cli()


@pytest.fixture
def salt_cli(master: SaltMaster) -> SaltCli:
    return master.get_salt_cli()


@pytest.fixture
def salt_call_cli(minion: SaltMinion) -> SaltCall:
    return minion.get_salt_call_cli()
