# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest
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
    ):
        with factory.started():
            yield factory
