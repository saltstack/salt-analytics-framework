# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import contextlib
import pathlib

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
try:
    from .version import __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0.not-installed"
    try:
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version

        with contextlib.suppress(PackageNotFoundError):
            __version__ = version(__name__)

    except ImportError:
        try:
            from pkg_resources import DistributionNotFound
            from pkg_resources import get_distribution

            with contextlib.suppress(DistributionNotFound):
                __version__ = get_distribution(__name__).version

        except ImportError:
            # pkg resources isn't even available?!
            pass

__all__ = ["__version__"]
