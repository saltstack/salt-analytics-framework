# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import shutil

import pytest
from saltfactories.daemons.master import SaltMaster
from saltfactories.daemons.minion import SaltMinion
from saltfactories.utils import random_string


@pytest.fixture(scope="module")
def temp_logs_dir(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("logs")
    yield tmp_dir
    shutil.rmtree(tmp_dir)


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
    ):
        with factory.started():
            yield factory
