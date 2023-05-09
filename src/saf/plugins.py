# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Salt Analytics Framework Plugins Support.
"""
from __future__ import annotations

import contextlib
import logging
import pathlib
import types
from typing import Generator
from typing import TypeVar

from salt.utils import entrypoints

log = logging.getLogger(__name__)


PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent

PLT = TypeVar("PLT", bound="PluginsList")


class PluginsList:
    """
    Plugins manager.
    """

    _instance = None

    def __init__(self: PLT) -> None:
        self.collectors: dict[str, types.ModuleType] = {}
        self.processors: dict[str, types.ModuleType] = {}
        self.forwarders: dict[str, types.ModuleType] = {}
        self.load_plugins()

    def __repr__(self: PLT) -> str:
        """
        Return a printable representation of the class instance.
        """
        return (
            f"<{self.__class__.__name__} collectors={list(self.collectors)} "
            f"processors={list(self.processors)} forwarders={list(self.forwarders)}>"
        )

    @staticmethod
    def instance() -> PluginsList:
        """
        Return the cached instance of the plugins listing.

        If it doesn't exist yet, a new instance is created and cached.
        """
        if PluginsList._instance is None:
            PluginsList._instance = PluginsList()
        return PluginsList._instance

    def load_plugins(self: PLT) -> None:
        """
        Load the available salt analytics framework plugins.
        """
        for name, listing in (
            ("collect", self.collectors),
            ("process", self.processors),
            ("forward", self.forwarders),
        ):
            for entry_point in entrypoints.iter_entry_points(f"saf.{name}"):
                log.debug("Loading salt analytics framework collect plugin from %s", entry_point)
                with catch_entry_points_exception(entry_point) as ctx:
                    module = entry_point.load()
                    if ctx.exception_caught:
                        continue
                    listing[entry_point.name] = module


@contextlib.contextmanager
def catch_entry_points_exception(entry_point: str) -> Generator[types.SimpleNamespace, None, None]:
    """
    Context manager to catch exceptions while loading entry points.
    """
    context = types.SimpleNamespace(exception_caught=False)
    try:
        yield context
    except Exception:
        context.exception_caught = True
        entry_point_details = entrypoints.name_and_version_from_entry_point(entry_point)
        log.exception(
            "Error processing Salt Analytics Framework Plugin %s(version: %s)",
            entry_point_details.name,
            entry_point_details.version,
        )
