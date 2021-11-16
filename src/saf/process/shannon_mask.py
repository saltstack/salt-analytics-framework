# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Mask data based using a length-relative normalized version of the Shannon Index as an indicator of entropy.
"""
import logging
import math
from typing import Any
from typing import Dict
from typing import Optional
from typing import Type

from pydantic import validator

from saf.models import CollectedEvent
from saf.models import ProcessConfigBase


log = logging.getLogger(__name__)


class ShannonMaskProcessConfig(ProcessConfigBase):
    """
    Configuration schema for the Shannon mask processor plugin.
    """

    mask_str: str = "HIGH-ENTROPY"
    mask_char: Optional[str]
    mask_prefix: str = "<:"
    mask_suffix: str = ":>"
    h_threshold: float = 0.9
    length_threshold: int = 16
    delimeter: str = " "
    alphabet: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="

    @validator("mask_char")
    def check_one_char(cls, v: str) -> str:
        """
        The mask character must be exactly one character.
        """
        if v:
            assert len(v) == 1
        return v

    @validator("h_threshold")
    def check_h_threshold_bounds(cls, v: float) -> float:
        """
        The Shannon threshold must be between 0 and 1, both inclusively.
        """
        assert v <= 1 and v >= 0
        return v

    @validator("length_threshold")
    def check_length_threshold_bounds(cls, v: int) -> int:
        """
        The length threshold should be greater than 1.

        Entropy on 1 character strings will always be maximal.
        """
        assert v > 1
        return v

    @validator("delimeter")
    def check_delimeter_one_char(cls, v: str) -> str:
        """
        The delimeter should be exactly one character.
        """
        assert len(v) == 1
        return v

    @validator("alphabet")
    def check_alphabet_more_than_one_char(cls, v: str) -> str:
        """
        We expect the alphabet to have more than one character.
        """
        assert len(v) > 1
        return v


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
        else:
            return f"{config.mask_prefix}{config.mask_str}{config.mask_suffix}"

    orig_str = event_piece

    try:
        split_piece = event_piece.split(config.delimeter)
        for word in split_piece:
            if len(word) >= config.length_threshold:
                h_norm = _calculate_normalized_shannon_index(word, config.alphabet)
                if h_norm > config.h_threshold:
                    event_piece = event_piece.replace(word, repl_fn(word))
    except Exception as exc:  # pylint: disable=broad-except
        log.error(f"Failed to mask value '{orig_str}' with message {exc}.  Skipping.")

    return event_piece


def _shannon_process(obj: Dict[str, Any], config: ShannonMaskProcessConfig) -> Dict[str, Any]:
    """
    Recursive method to iterate over dictionary and apply rules to all str values.
    """
    # Iterate over all attributes of obj.  If string, do mask.  If dict, recurse.  Else, do nothing.
    for key, value in obj.items():
        if isinstance(value, str):
            obj[key] = _shannon_mask(value, config)
        elif isinstance(value, dict):
            obj[key] = _shannon_process(value, config)
    return obj


async def process(  # pylint: disable=unused-argument
    *,
    config: ShannonMaskProcessConfig,
    event: CollectedEvent,
) -> CollectedEvent:
    """
    Method called to mask the data based on provided regex rules.
    """
    log.info(f"Processing event in shannon_mask: {event.json()}")
    event_dict = event.dict()
    processed_event_dict = _shannon_process(event_dict, config)
    processed_event = event.parse_obj(processed_event_dict)
    return processed_event
