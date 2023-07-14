# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import pytest
from saltfactories.daemons.master import SaltMaster
from saltfactories.daemons.minion import SaltMinion
from saltfactories.utils import random_string

from saf.utils.salt import MasterClient
from saf.utils.salt import MinionClient


@pytest.fixture(scope="module")
def minion(master: SaltMaster) -> SaltMinion:
    factory = master.salt_minion_daemon(random_string("minion-"))
    with factory.started():
        yield factory


@pytest.mark.asyncio
async def test_master_client(master, minion):
    client = MasterClient(master.config)
    ret = await client.cmd(minion.id, "test.ping")
    assert minion.id in ret
    assert ret[minion.id] is True


@pytest.mark.asyncio
async def test_minion_client_from_master(master):
    client = MinionClient(master.config)
    ret = await client.cmd("test.ping")
    assert ret is True


@pytest.mark.asyncio
async def test_cmd_from_minion(minion):
    client = MinionClient(minion.config)
    ret = await client.cmd("test.ping")
    assert ret is True
