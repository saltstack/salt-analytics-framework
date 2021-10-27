# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pathlib

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
try:
    from .version import __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0.not-installed"
    try:
        from importlib.metadata import version  # type: ignore [attr-defined]
        from importlib.metadata import PackageNotFoundError  # type: ignore [attr-defined]

        try:
            __version__ = version(__name__)
        except PackageNotFoundError:
            # package is not installed
            pass
    except ImportError:
        try:
            from pkg_resources import get_distribution
            from pkg_resources import DistributionNotFound

            try:
                __version__ = get_distribution(__name__).version
            except DistributionNotFound:
                # package is not installed
                pass
        except ImportError:
            # pkg resources isn't even available?!
            pass
