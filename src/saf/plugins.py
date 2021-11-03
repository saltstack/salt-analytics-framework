# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Salt Analytics Framework Plugins Support.
"""
import contextlib
import logging
import pathlib
import types
from typing import Dict
from typing import Generator

from salt.utils import entrypoints

log = logging.getLogger(__name__)


PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent


class PluginsList:
    """
    Plugins manager.
    """

    _instance = None

    def __init__(self) -> None:
        self.collectors: Dict[str, types.ModuleType] = {}
        self.processors: Dict[str, types.ModuleType] = {}
        self.forwarders: Dict[str, types.ModuleType] = {}
        self.load_plugins()

    def __repr__(self) -> str:
        """
        Return a printable representation of the class instance.
        """
        return (
            f"<{self.__class__.__name__} collectors={list(self.collectors)} "
            f"processors={list(self.processors)} forwarders={list(self.forwarders)}>"
        )

    @staticmethod
    def instance() -> "PluginsList":
        """
        Return the cached instance of the plugins listing.

        If it doesn't exist yet, a new instance is created and cached.
        """
        if PluginsList._instance is None:
            PluginsList._instance = PluginsList()
        return PluginsList._instance

    def load_plugins(self) -> None:
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
    except Exception as exc:  # pylint: disable=broad-except
        context.exception_caught = True
        entry_point_details = entrypoints.name_and_version_from_entry_point(entry_point)
        log.error(
            "Error processing Salt Analytics Framework Plugin %s(version: %s): %s",
            entry_point_details.name,
            entry_point_details.version,
            exc,
            exc_info_on_loglevel=logging.DEBUG,
        )
