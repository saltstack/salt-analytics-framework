# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
A log collector plugin.
"""
from __future__ import annotations

import asyncio
import logging
import os
import pathlib
import re
from typing import Any
from typing import AsyncIterator
from typing import Dict
from typing import List
from typing import Optional
from typing import Pattern
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from pydantic.class_validators import validator
from pydantic.main import BaseModel

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


LCC = TypeVar("LCC", bound="LogCollectConfig")


class LogCollectConfig(CollectConfigBase):
    """
    Configuration schema for the log collect plugin.
    """

    path: pathlib.Path
    log_format: Optional[str]
    parse_config: Optional[pathlib.Path]
    backfill: bool = True
    wait: float = 5

    @validator("parse_config")
    @classmethod
    def _ensure_log_format_for_parsing(
        cls: Type[LCC], value: pathlib.Path, values: Dict[str, Any]
    ) -> pathlib.Path:
        if value and not values["log_format"]:
            msg = "Parsing without specifying a log_format is not allowed!"
            raise ValueError(msg)
        return value


class DrainResult(BaseModel):
    """
    Wrapper around parsing results.
    """

    log_cluster: Dict[str, Any]
    parameters: List[str]


class LogCollectedEvent(CollectedEvent):
    """
    Collected event subclass to hold logs collector results.
    """

    drain_result: Optional[DrainResult]
    groups: Optional[Dict[Any, Any]]


def get_config_schema() -> Type[LogCollectConfig]:
    """
    Get the log plugin configuration schema.
    """
    return LogCollectConfig


def _generate_log_format_regex(log_format: str) -> Tuple[List[Union[str, Any]], Pattern[str]]:
    """
    Function to generate regular expression to split log messages.

    Taken and adapted from https://github.com/logpai/logparser/
    """
    headers = []
    # Split by <header> instances
    sliced = re.split(r"(<[^<>]+>)", log_format)
    pre_regex = ""
    for _slice in sliced:
        if "<" not in _slice:
            new_slice = re.sub(" +", "\\\\s+", _slice)
            pre_regex += new_slice
        else:
            # Get the header name from between the angled brackets
            header = _slice.strip("<").strip(">")
            headers.append(header)
            # Create a named group within the new regex
            pre_regex += f"(?P<{header}>.*?)"
    # Make sure to account for the start and end of the line
    regex = re.compile("^" + pre_regex + "$")
    return headers, regex


async def collect(*, ctx: PipelineRunContext[LogCollectConfig]) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect log events.
    """
    config = ctx.config
    try:
        parsing = bool(config.parse_config)

        if config.log_format:
            headers, format_regex = _generate_log_format_regex(config.log_format)

        if parsing:
            log.info("Logs collector will be parsing using config at %s", config.parse_config)

            # Initialize the TemplateMiner
            drain3_config = TemplateMinerConfig()
            drain3_config.load(config.parse_config)
            template_miner = TemplateMiner(config=drain3_config)
        else:
            log.info("Logs collector will NOT be parsing")

        with config.path.open(mode="r") as rfh:
            # If we do not need to gather older logs, we put the cursor at the end of file
            if not config.backfill:
                rfh.seek(0, os.SEEK_END)
            while True:
                line = rfh.readline().strip()
                if not line:
                    await asyncio.sleep(config.wait)
                else:
                    groups = None
                    if config.log_format:
                        # Split by headers
                        match = format_regex.search(line.strip())
                        if match:
                            groups = {header: match.group(header) for header in headers}

                    if parsing and match:
                        # Parse only the content
                        content = match.group("Content")
                        result = template_miner.add_log_message(content)

                        # Create the DrainResult
                        parameters = template_miner.get_parameter_list(
                            result["template_mined"], content
                        )
                        drain_result = DrainResult(log_cluster=result, parameters=parameters)
                        event = LogCollectedEvent(
                            data={"log_line": line}, groups=groups, drain_result=drain_result
                        )
                    else:
                        event = LogCollectedEvent(data={"log_line": line}, groups=groups)
                    yield event

    except FileNotFoundError as exc:
        log.debug("File %s not found", exc.filename)
