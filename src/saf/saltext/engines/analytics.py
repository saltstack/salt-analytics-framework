# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""
Salt engine module.
"""
import asyncio
import logging
import pathlib
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

import aiorun
from salt.utils import yaml

from saf.manager import Manager
from saf.models import AnalyticsConfig

if TYPE_CHECKING:
    __salt__: Dict[str, Callable[..., Any]]
    __opts__: Dict[str, Any]
    __salt_system_encoding__: str

log = logging.getLogger(__name__)


__virtualname__ = "analytics"


def __virtual__() -> Union[str, Tuple[bool, str]]:
    """
    Return the module name, or ``(False, "Failure reason")`` to load, or not, the engine.
    """
    # To force a module not to load return something like:
    #   return (False, "The salt-analytics-framework engine module is not implemented yet")
    if get_config_dict() is None:
        return False, "Could not find any valid salt analytics configuration"
    return __virtualname__


def get_config_dict() -> Optional[Dict[str, Any]]:
    """
    Return the configuration dictionary for salt analytics.
    """
    config_dict: Optional[Dict[str, Any]]
    config_dict = __salt__["config.get"]("analytics")
    if not config_dict:
        config_dir = pathlib.Path(__opts__["config_dir"])
        config_file = config_dir / "analytics"
        config_dict = yaml.safe_load(config_file.read_text(encoding=__salt_system_encoding__))
    if config_dict:
        config_dict["salt_config"] = __opts__.copy()
    return config_dict


def start() -> None:
    """
    Start the salt analytics engine.
    """
    config = AnalyticsConfig.parse_obj(get_config_dict())
    manager = Manager(config)
    aiorun.run(
        manager.run(),
        loop=asyncio.get_event_loop(),
        stop_on_unhandled_errors=True,
        shutdown_callback=manager.await_stopped(),
    )
