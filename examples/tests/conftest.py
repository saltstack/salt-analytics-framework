# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import os
import pathlib
import sys
from typing import Any

import pytest

TESTS_DIR = pathlib.Path(__file__).resolve().parent
CODE_DIR = TESTS_DIR.parent.parent

# Coverage
if "COVERAGE_PROCESS_START" in os.environ:
    MAYBE_RUN_COVERAGE = True
    COVERAGERC_FILE = os.environ["COVERAGE_PROCESS_START"]
else:
    COVERAGERC_FILE = str(CODE_DIR / ".coveragerc")
    MAYBE_RUN_COVERAGE = sys.argv[0].endswith("pytest.py") or "_COVERAGE_RCFILE" in os.environ
    if MAYBE_RUN_COVERAGE:
        # Flag coverage to track suprocesses by pointing it to the right .coveragerc file
        os.environ["COVERAGE_PROCESS_START"] = str(COVERAGERC_FILE)


# ----- PyTest Tempdir Plugin Hooks -------------------------------------------------------------->
def pytest_tempdir_basename() -> str:
    """
    Return the temporary directory basename for the salt test suite.
    """
    return "analytics"


# <---- PyTest Tempdir Plugin Hooks ---------------------------------------------------------------


@pytest.fixture(scope="session")
def salt_factories_config() -> dict[str, Any]:
    """
    Return a dictionary with the keyword arguments for FactoriesManager.
    """
    if os.environ.get("CI"):
        start_timeout = 120
    else:
        start_timeout = 60
    if os.environ.get("ONEDIR_TESTRUN", "0") == "1":
        code_dir = None
    else:
        code_dir = str(CODE_DIR)

    kwargs = {
        "code_dir": code_dir,
        "start_timeout": start_timeout,
        "inject_sitecustomize": MAYBE_RUN_COVERAGE,
    }
    if MAYBE_RUN_COVERAGE:
        kwargs["coverage_rc_path"] = str(COVERAGERC_FILE)
    else:
        kwargs["coverage_rc_path"] = None
    kwargs["coverage_db_path"] = os.environ.get("COVERAGE_FILE")
    return kwargs
