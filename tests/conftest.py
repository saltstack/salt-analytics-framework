# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import os
from typing import Any
from typing import Dict

import pytest

from saf import PACKAGE_ROOT


@pytest.fixture(scope="session")
def salt_factories_config() -> Dict[str, Any]:
    """
    Return a dictionary with the keyword arguments for FactoriesManager.
    """
    return {
        "code_dir": str(PACKAGE_ROOT),
        "inject_coverage": "COVERAGE_PROCESS_START" in os.environ,
        "inject_sitecustomize": "COVERAGE_PROCESS_START" in os.environ,
        "start_timeout": 120 if os.environ.get("CI") else 60,
    }
