# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
A log collector plugin.
"""
import asyncio
import logging
import os
import pathlib
from typing import AsyncIterator
from typing import Optional
from typing import Type

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from salt.utils.files import fopen

from saf.models import CollectConfigBase
from saf.models import CollectedEvent


log = logging.getLogger(__name__)


class LogCollectConfig(CollectConfigBase):
    """
    Configuration schema for the log collect plugin.
    """

    path: pathlib.Path
    parse_config: Optional[pathlib.Path] = None
    backfill: bool = True
    wait: float = 5


def get_config_schema() -> Type[LogCollectConfig]:
    """
    Get the log plugin configuration schema.
    """
    return LogCollectConfig


async def collect(*, config: LogCollectConfig) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect log events.
    """
    try:
        parsing = True if config.parse_config else False
        if parsing:
            log.info(f"Logs collector will be parsing using config at {config.parse_config}")
            drain3_config = TemplateMinerConfig()
            drain3_config.load(config.parse_config)
            template_miner = TemplateMiner(config=drain3_config)
        else:
            log.info("Logs collector will NOT be parsing")

        with config.path.open(mode="r") as fp:
            # If we do not need to gather older logs, we put the cursor at the end of file
            if not config.backfill:
                fp.seek(0, os.SEEK_END)
            while True:
                line = fp.readline().strip()
                if not line:
                    await asyncio.sleep(config.wait)
                else:
                    if parsing:
                        result = template_miner.add_log_message(line)
                        event = CollectedEvent(data={"log_line": line, "template": result})
                        if result["change_type"] != "none":
                            log.info(f"Following changed in drain template miner: {result}")
                    else:
                        event = CollectedEvent(data={"log_line": line})
                    yield event

    except FileNotFoundError as exc:
        log.debug(f"File {exc.filename} not found")
