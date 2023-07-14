# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""
Define the version.
"""
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
            __version__ = version("salt-analytics.examples")

    except ImportError:
        try:
            from pkg_resources import DistributionNotFound
            from pkg_resources import get_distribution

            with contextlib.suppress(DistributionNotFound):
                __version__ = get_distribution("salt-analytics.examples").version

        except ImportError:
            # pkg resources isn't even available?!
            pass
