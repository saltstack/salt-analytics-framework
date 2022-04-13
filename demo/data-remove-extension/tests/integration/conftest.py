# Copyright 2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest


@pytest.fixture(scope="package")
def master(master):
    with master.started():
        yield master


@pytest.fixture(scope="package")
def minion(minion):
    with minion.started():
        yield minion


@pytest.fixture
def salt_run_cli(master):
    return master.salt_run_cli()


@pytest.fixture
def salt_cli(master):
    return master.salt_cli()


@pytest.fixture
def salt_call_cli(minion):
    return minion.salt_call_cli()
