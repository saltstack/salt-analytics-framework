# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Mask data based on provided regex rules.
"""
import logging
import re
from typing import Any
from typing import Dict
from typing import Match
from typing import Optional
from typing import Type

from pydantic import Field

from saf.models import CollectedEvent
from saf.models import ProcessConfigBase


log = logging.getLogger(__name__)


class RegexMaskProcessConfig(ProcessConfigBase):
    """
    Configuration schema for the regex mask processor plugin.
    """

    rules: Dict[str, str]
    mask_char: Optional[str] = Field(min_length=1, max_length=1)
    mask_prefix: str = "<:"
    mask_suffix: str = ":>"


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the regex mask processor plugin configuration schema.
    """
    return RegexMaskProcessConfig


def _regex_mask(event_piece: str, config: RegexMaskProcessConfig) -> str:
    """
    Go through the string and process based on regex rules.
    """

    def repl_fn(match: Match[Any]) -> str:
        """
        The replacement function to be called on each match.

        If a mask_char was provided, use that with matching length.
        Otherwise, use the rule name surrounded by prefix and suffix.
        """
        if config.mask_char:
            matched_str = match.group(0)
            return config.mask_char * len(matched_str)
        else:
            return f"{config.mask_prefix}{rule_name}{config.mask_suffix}"

    orig_str = event_piece

    try:
        for rule_name, pattern in config.rules.items():
            event_piece = re.sub(pattern, repl_fn, event_piece)
    except Exception as exc:  # pylint: disable=broad-except
        log.error(f"Failed to mask value '{orig_str}' with message {exc}.  Skipping.")

    return event_piece


def _regex_process(obj: Any, config: RegexMaskProcessConfig) -> Any:
    """
    Recursive method to iterate over dictionary and apply rules to all str values.
    """
    # Iterate over all attributes of obj.  If string, do mask.  If dict, set, tuple, or list -> recurse.
    if isinstance(obj, str):
        return _regex_mask(obj, config)
    elif isinstance(obj, (list, tuple, set)):
        klass = type(obj)
        return klass(_regex_process(i, config) for i in obj)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = _regex_process(value, config)
    return obj


async def process(  # pylint: disable=unused-argument
    *,
    config: RegexMaskProcessConfig,
    event: CollectedEvent,
) -> CollectedEvent:
    """
    Method called to mask the data based on provided regex rules.
    """
    log.info("Processing event in regex_mask: %s", event.json())
    event_dict = event.dict()
    processed_event_dict = _regex_process(event_dict, config)
    processed_event = event.parse_obj(processed_event_dict)
    return processed_event
