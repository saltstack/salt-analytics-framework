# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import pathlib
import shutil
from typing import Iterator

import pytest
from saltfactories.cli.run import SaltRun
from saltfactories.cli.salt import SaltCli
from saltfactories.daemons.master import SaltMaster
from saltfactories.daemons.minion import SaltMinion
from saltfactories.utils import random_string


@pytest.fixture(scope="module", autouse=True)
def minion(
    master: SaltMaster, analytics_events_dump_directory, analytics_config_contents
) -> SaltMinion:
    default_config = {
        "engines": ["analytics"],
    }
    factory = master.salt_minion_daemon(random_string("minion-"), defaults=default_config)
    with pytest.helpers.temp_file(
        "analytics", contents=analytics_config_contents, directory=factory.config_dir
    ), factory.started():
        yield factory


@pytest.fixture(scope="package")
def analytics_events_dump_directory(tmp_path_factory) -> Iterator[pathlib.Path]:
    dump_path = tmp_path_factory.mktemp("analytics-events-dump")
    try:
        yield dump_path
    finally:
        shutil.rmtree(str(dump_path), ignore_errors=True)


@pytest.fixture(autouse=True)
def cleanup_analytics_events_dump_directory(
    analytics_events_dump_directory: pathlib.Path,
) -> Iterator[pathlib.Path]:
    try:
        yield analytics_events_dump_directory
    finally:
        for path in analytics_events_dump_directory.iterdir():
            path.unlink()


@pytest.fixture(scope="package")
def master(salt_factories, analytics_events_dump_directory) -> SaltMaster:
    factory = salt_factories.salt_master_daemon(random_string("master-"))
    with factory.started():
        yield factory


@pytest.fixture()
def salt_run_cli(master: SaltMaster) -> SaltRun:
    return master.get_salt_run_cli()


@pytest.fixture()
def salt_cli(master: SaltMaster) -> SaltCli:
    return master.get_salt_cli()
