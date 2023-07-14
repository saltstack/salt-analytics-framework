# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import pytest
import salt.config

from saf.utils.salt import MasterClient
from saf.utils.salt import MinionClient


@pytest.fixture
def minion_opts(tmp_path):
    """
    Default minion configuration with relative temporary paths to not require root permissions.
    """
    root_dir = tmp_path / "minion"
    opts = salt.config.DEFAULT_MINION_OPTS.copy()
    opts["__role"] = "minion"
    opts["root_dir"] = str(root_dir)
    for name in ("cachedir", "pki_dir", "sock_dir", "conf_dir"):
        dirpath = root_dir / name
        dirpath.mkdir(parents=True)
        opts[name] = str(dirpath)
    opts["log_file"] = "logs/minion.log"
    return opts


def test_master_client_runtime_error_on_wrong_role():
    opts = {"__role": "minion"}
    with pytest.raises(RuntimeError):
        MasterClient(opts)


@pytest.mark.asyncio
async def test_minin_client_missing_func(minion_opts):
    client = MinionClient(minion_opts)
    with pytest.raises(RuntimeError):
        await client.cmd("this_func.does_not_exist")
