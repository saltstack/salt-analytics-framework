# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Mask data based on provided regex rules.
"""
from __future__ import annotations

import functools
import logging
import re
from typing import Any
from typing import AsyncIterator
from typing import Dict
from typing import Match
from typing import Optional
from typing import Type
from typing import TypeVar

from pydantic import Field

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

log = logging.getLogger(__name__)

RegexProcessObject = TypeVar("RegexProcessObject")


class RegexMaskProcessConfig(ProcessConfigBase):
    """
    Configuration schema for the regex mask processor plugin.
    """

    rules: Dict[str, str]
    mask_char: Optional[str] = Field(None, min_length=1, max_length=1)
    mask_prefix: str = Field(default="<:")
    mask_suffix: str = Field(default=":>")


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the regex mask processor plugin configuration schema.
    """
    return RegexMaskProcessConfig


def _regex_mask(event_piece: str, config: RegexMaskProcessConfig) -> str:
    """
    Go through the string and process based on regex rules.
    """

    def repl_fn(rule_name: str, match: Match[Any]) -> str:
        """
        The replacement function to be called on each match.

        If a mask_char was provided, use that with matching length.
        Otherwise, use the rule name surrounded by prefix and suffix.
        """
        if config.mask_char:
            matched_str = match.group(0)
            return config.mask_char * len(matched_str)
        return f"{config.mask_prefix}{rule_name}{config.mask_suffix}"

    orig_str = event_piece

    try:
        for rule_name, pattern in config.rules.items():
            event_piece = re.sub(pattern, functools.partial(repl_fn, rule_name), event_piece)
    except Exception:
        log.exception("Failed to mask value '%s'", orig_str)

    return event_piece


def _regex_process(
    obj: str | list[Any] | tuple[Any, ...] | set[Any] | Dict[str, Any],
    config: RegexMaskProcessConfig,
) -> str | list[Any] | tuple[Any, ...] | set[Any] | Dict[str, Any]:
    """
    Recursive method to iterate over dictionary and apply rules to all str values.
    """
    # Iterate over all attributes of obj.
    # If string, do mask.
    # If dict, set, tuple, or list -> recurse.
    if isinstance(obj, str):
        return _regex_mask(obj, config)
    if isinstance(obj, (list, tuple, set)):
        klass = type(obj)
        return klass(_regex_process(i, config) for i in obj)
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = _regex_process(value, config)
    return obj


async def process(
    *,
    ctx: PipelineRunContext[RegexMaskProcessConfig],
    event: CollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Method called to mask the data based on provided regex rules.
    """
    config = ctx.config
    log.debug("Processing event in regex_mask: %s", event.model_dump_json())
    event_dict = event.model_dump()
    processed_event_dict = _regex_process(event_dict, config)
    yield event.model_validate(processed_event_dict)
