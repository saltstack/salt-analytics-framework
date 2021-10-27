# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
# type: ignore [attr-defined]
import pytest

import saf.salt.engines.saf_mod as saf_engine


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"this_does_not_exist.please_replace_it": lambda: True},
    }
    return {
        saf_engine: module_globals,
    }


def test_replace_this_this_with_something_meaningful():
    assert "this_does_not_exist.please_replace_it" in saf_engine.__salt__
    assert saf_engine.__salt__["this_does_not_exist.please_replace_it"]() is True
