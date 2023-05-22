# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from saf.forward import test


def test_mutually_exclusive_parameters(tmp_path):
    with pytest.raises(ValueError, match=".* mutually exclusive .*"):
        test.TestForwardConfig(
            plugin="test",
            path=tmp_path,
            add_event_to_shared_cache=True,
        )
