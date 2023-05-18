# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""
Salt engine module.
"""
from __future__ import annotations

import asyncio
import logging
import pathlib
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

import aiorun
from salt.utils import yaml

from saf.manager import Manager
from saf.models import AnalyticsConfig

if TYPE_CHECKING:
    __salt__: dict[str, Callable[..., Any]]
    __opts__: dict[str, Any]
    __salt_system_encoding__: str

log = logging.getLogger(__name__)


__virtualname__ = "analytics"


def __virtual__() -> str | tuple[bool, str]:
    """
    Return the module name, or ``(False, "Failure reason")`` to load, or not, the engine.
    """
    # To force a module not to load return something like:
    #   return (False, "The salt-analytics-framework engine module is not implemented yet")
    if get_config_dict() is None:
        return False, "Could not find any valid salt analytics configuration"
    return __virtualname__


def get_config_dict() -> dict[str, Any] | None:
    """
    Return the configuration dictionary for salt analytics.
    """
    config_dict: dict[str, Any] | None
    config_dict = __salt__["config.get"]("analytics")  # pylint: disable=undefined-variable
    if not config_dict:
        config_dir = pathlib.Path(__opts__["config_dir"])  # pylint: disable=undefined-variable
        config_file = config_dir / "analytics"
        if config_file.exists():
            config_dict = yaml.safe_load(
                config_file.read_text(
                    encoding=__salt_system_encoding__,  # pylint: disable=undefined-variable
                )
            )
    if config_dict:
        config_dict["salt_config"] = __opts__.copy()
    return config_dict


def start() -> None:
    """
    Start the salt analytics engine.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    config = AnalyticsConfig.parse_obj(get_config_dict())
    manager = Manager(config)
    aiorun.run(
        manager.run(),
        loop=loop,
        stop_on_unhandled_errors=True,
        shutdown_callback=manager.await_stopped(),
    )
