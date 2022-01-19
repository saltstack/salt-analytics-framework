# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Test forwarder plugin.

The test forward plugin exists as an implementation example and also to be able
to test the salt-analytics-framework

It doesn't really do anything to the collected event.
"""
import asyncio
import json
import logging
import pathlib
from typing import Optional
from typing import Type

from saf.models import CollectedEvent
from saf.models import ForwardConfigBase


log = logging.getLogger(__name__)


class TestForwardConfig(ForwardConfigBase):
    """
    Test forwarder configuration.
    """

    sleep: float = 0.0
    path: Optional[pathlib.Path] = None
    message: Optional[str] = None
    dump_event: bool = False


def get_config_schema() -> Type[TestForwardConfig]:
    """
    Get the noop plugin configuration schema.
    """
    return TestForwardConfig


async def forward(
    *,
    config: TestForwardConfig,
    event: CollectedEvent,
) -> None:
    """
    Method called to forward the event.
    """
    log.info("Forwarding using %s: %s", config.name, event)
    assert event
    if config.sleep > 0:
        await asyncio.sleep(config.sleep)
    if config.path:
        if config.message:
            if config.dump_event:
                dump_text = json.dumps({config.message: event.dict()})
            else:
                dump_text = config.message
        elif config.dump_event:
            dump_text = event.json()
        else:
            dump_text = ""
        log.info("Writing into %s. Contents: %s", config.path, dump_text)
        with config.path.open("a", encoding="utf-8") as wfh:
            wfh.write(dump_text + "\n")
    log.info("Forwarded using %s: %s", config.name, event)
