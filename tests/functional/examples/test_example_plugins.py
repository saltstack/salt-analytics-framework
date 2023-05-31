# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

from saf.plugins import PluginsList


def test_example_plugins_available():
    plugins_list = PluginsList()
    assert "mnist_digits" in plugins_list.collectors
    assert "mnist_network" in plugins_list.processors
