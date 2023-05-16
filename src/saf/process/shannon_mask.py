# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Mask data based using a length-relative normalized version of the Shannon Index as an indicator of entropy.
"""
from __future__ import annotations

import logging
import math
import string
from typing import Any
from typing import AsyncIterator
from typing import Optional
from typing import Type

from pydantic import Field

from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

log = logging.getLogger(__name__)


class ShannonMaskProcessConfig(ProcessConfigBase):
    """
    Configuration schema for the Shannon mask processor plugin.
    """

    mask_str: str = "HIGH-ENTROPY"
    mask_char: Optional[str] = Field(min_length=1, max_length=1)
    mask_prefix: str = "<:"
    mask_suffix: str = ":>"
    h_threshold: float = Field(0.9, ge=0.0, le=1.0)
    length_threshold: int = Field(16, gt=1)
    delimeter: str = Field(" ", min_length=1, max_length=1)
    alphabet: str = Field(f"{string.ascii_letters}{string.digits}+/=", min_length=1)


def get_config_schema() -> Type[ProcessConfigBase]:
    """
    Get the Shannon mask processor plugin configuration schema.
    """
    return ShannonMaskProcessConfig


def _calculate_normalized_shannon_index(word: str, alphabet: str) -> float:
    """
    Calculate a length-relative normalized Shannon index of the event_piece.

    Shannon Diversity index: https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/shannon.htm
    """
    # pylint: disable=invalid-name
    word_len = len(word)
    alphabet_len = len(alphabet)
    p_dict = {i: word.count(i) / word_len for i in word if i in alphabet}
    # h is the standard Shannon Index naming convention
    h = sum(-1 * p_i * math.log(p_i) for p_i in p_dict.values())

    # Quotient-Remainder Thm: We have integers d, r such that
    # len(word) = d * len(alphabet) + r where 0 <= r < len(alphabet)
    # We can use this relationship to find h_max for a given string length.
    d = word_len // alphabet_len
    r = word_len % alphabet_len
    p_r = (d + 1) / word_len
    p_d = d / word_len
    h_max = -(r * p_r * math.log(p_r)) - ((alphabet_len - r) * p_d * math.log(p_d))
    return h / h_max
    # pylint: enable=invalid-name


def _shannon_mask(event_piece: str, config: ShannonMaskProcessConfig) -> str:
    """
    Go through the string and process based on normalized Shannon index values.
    """

    def repl_fn(word: str) -> str:
        """
        The replacement function to be called on each match.

        If a mask_char was provided, use that with matching length.
        Otherwise, use the config.mask_str surrounded by prefix and suffix.
        """
        if config.mask_char:
            return config.mask_char * len(word)
        return f"{config.mask_prefix}{config.mask_str}{config.mask_suffix}"

    orig_str = event_piece

    try:
        split_piece = event_piece.split(config.delimeter)
        for word in split_piece:
            if len(word) >= config.length_threshold:
                h_norm = _calculate_normalized_shannon_index(word, config.alphabet)
                if h_norm > config.h_threshold:
                    event_piece = event_piece.replace(word, repl_fn(word))
    except Exception:
        log.exception("Failed to mask value '%s'", orig_str)

    return event_piece


def _shannon_process(obj: Any, config: ShannonMaskProcessConfig) -> Any:  # noqa: ANN401
    """
    Recursive method to iterate over dictionary and apply rules to all str values.
    """
    # Iterate over all attributes of obj.  If string, do mask.  If dict, recurse.  Else, do nothing.
    if isinstance(obj, str):
        return _shannon_mask(obj, config)
    if isinstance(obj, (list, tuple, set)):
        klass = type(obj)
        return klass(_shannon_process(i, config) for i in obj)
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = _shannon_process(value, config)
    return obj


async def process(
    *,
    ctx: PipelineRunContext[ShannonMaskProcessConfig],
    event: CollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Method called to mask the data based on normalized Shannon index values.
    """
    config = ctx.config
    log.info("Processing event in shannon_mask: %s", event.json())
    event_dict = event.dict()
    processed_event_dict = _shannon_process(event_dict, config)
    yield event.parse_obj(processed_event_dict)
