# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
A collect plugin that simply collects the output of a salt execution module.
"""
import asyncio
import logging
from typing import Any
from typing import AsyncIterator
from typing import Dict
from typing import List
from typing import Type

import salt.loader

from saf.models import CollectConfigBase
from saf.models import CollectedEvent


log = logging.getLogger(__name__)


class SaltExecConfig(CollectConfigBase):
    """
    Configuration schema for the salt_exec collect plugin.
    """

    interval: float = 5
    fn: str = "test.ping"
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}


def get_config_schema() -> Type[SaltExecConfig]:
    """
    Get the salt_exec plugin configuration schema.
    """
    return SaltExecConfig


async def collect(*, config: SaltExecConfig) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect events.
    """
    # Load salt functions and pick out the desired one
    loaded_funcs = salt.loader.minion_mods(config.parent.salt_config)
    loaded_fn = loaded_funcs[config.fn]

    while True:
        ret = loaded_fn(*config.args, **config.kwargs)
        event = CollectedEvent(data={"ret": ret})
        log.info("CollectedEvent: %s", event)
        yield event
        await asyncio.sleep(config.interval)
