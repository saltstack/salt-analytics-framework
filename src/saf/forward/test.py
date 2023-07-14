# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Test forwarder plugin.

The test forward plugin exists as an implementation example and also to be able
to test the salt-analytics-framework

It doesn't really do anything to the collected event.
"""
from __future__ import annotations

import asyncio
import json
import logging
import pathlib
from typing import Any
from typing import Optional
from typing import Type

from pydantic import model_validator

from saf.models import CollectedEvent
from saf.models import ForwardConfigBase
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class TestForwardConfig(ForwardConfigBase):
    """
    Test forwarder configuration.
    """

    sleep: float = 0.0
    path: Optional[pathlib.Path] = None
    message: Optional[str] = None
    dump_event: bool = False
    add_event_to_shared_cache: bool = False

    @model_validator(mode="before")
    @classmethod
    def _check_mutually_exclusive_parameters(
        cls: Type[TestForwardConfig], values: dict[str, Any]
    ) -> dict[str, Any]:
        path = values.get("path")
        add_event_to_shared_cache = values.get("add_event_to_shared_cache") or False
        if path and add_event_to_shared_cache:
            msg = "The 'path' and 'add_event_to_shared_cache' are mutually exclusive"
            raise ValueError(msg)
        return values


def get_config_schema() -> Type[TestForwardConfig]:
    """
    Get the noop plugin configuration schema.
    """
    return TestForwardConfig


async def forward(
    *,
    ctx: PipelineRunContext[TestForwardConfig],
    event: CollectedEvent,
) -> None:
    """
    Method called to forward the event.
    """
    config = ctx.config
    log.info("Forwarding using %s: %s", config.name, event)
    if config.sleep > 0:
        await asyncio.sleep(config.sleep)
    if config.add_event_to_shared_cache:
        log.info(
            "Storing collected events in `pipeline.shared_cache` under "
            "the 'collected_events' key."
        )
        if "collected_events" not in ctx.shared_cache:
            ctx.shared_cache["collected_events"] = []
        ctx.shared_cache["collected_events"].append(event)
    elif config.path:
        if config.message:
            if config.dump_event:
                dump_text = json.dumps({config.message: event.model_dump()})
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
