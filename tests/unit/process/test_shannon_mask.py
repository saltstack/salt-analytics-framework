# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import copy
from typing import Any

import pytest

from saf.models import CollectedEvent
from saf.process.shannon_mask import ShannonMaskProcessConfig
from saf.process.shannon_mask import _calculate_normalized_shannon_index
from saf.process.shannon_mask import _shannon_process


class SubclassedCollectedEvent(CollectedEvent):
    """
    A subclass of CollectedEvent to allow recursive testing of Shannon masker.
    """

    new_field: CollectedEvent


@pytest.fixture
def data() -> dict[str, Any]:
    data = {
        "high_hex_entropy": "I'm gonna make him an 000123456789abcdef0123456789abcdefdab he can't refuse.",
        "nothing": "",
        "no_repl": "Here's looking at you, kid.",
    }
    return data


@pytest.fixture
def sub_data() -> dict[str, Any]:
    sub_data = {
        "ip_address": "My IP is 127.0.0.1",
        "integer": 12,
        "zero_hex_entropy": "What is the airspeed velocity of an unladen swallow? aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "list_test": [
            "not bad stuff",
            "bad stuff d37a6115d8972f960fec0be035b44a2dab08c",
            "more good stuff",
        ],
        "tuple_test": ("not bad stuff", "bad stuff a244ac72d869901ba830635ed10e5bcdffb70"),
        "set_test": {
            "not bad stuff",
            "bad stuff 685865eafa2f3077db3a110c9bd0b2c9ed440",
            "more good stuff",
        },
    }
    return sub_data


def validate_shannon_assumptions() -> None:
    """
    We need to ensure the diversity metric we are using always follows the following assumptions.

    1.  The highest value, h_max, occurs when all characters in the alphabet occur at
        the minimum frequency relative to string length.  We only calculate frequencies for letters
        within the alphabet.
            - ex. If our alphabet has 64 letters, and we have a 256 = 64 * 4 character string,
            h_max occurs when each character appears exactly four times.

    2.  The minimum value, h_min, occurs when there is only one unique character in the string.
            -ex. 'aaaaaaaaaaaaaaaaaaa'

    3.  Replacing one instance of an over-represented character with an under-represented one
        should not reduce the metric's value
            - ex. metric('aabbbc') <= metric('aabbc')
    """
    alphabet = "0123456789abcdef"
    test_string = list("0123456789abcdef0123456789abcdef0352")
    shannon_values = []

    for i in range(len(test_string)):  # pylint: disable=consider-using-enumerate
        test_string[i] = "0"
        shannon_values.append(_calculate_normalized_shannon_index("".join(test_string), alphabet))

    for i in range(len(shannon_values) - 1):  # pylint: disable=consider-using-enumerate
        assert shannon_values[i] >= shannon_values[i + 1]

    assert shannon_values[0] == 1
    assert shannon_values[-1] == 0


def test__shannon_process(data: dict[str, Any], sub_data: dict[str, Any]) -> None:
    """
    Make sure it catches and replaces correctly with the mask_str.
    """
    config = ShannonMaskProcessConfig(
        plugin="shannon-mask-processor",
        mask_str="offer",
        mask_prefix="",
        mask_suffix="",
        alphabet="0123456789abcdef",
    )
    masked_data = copy.deepcopy(data)
    masked_sub_data = copy.deepcopy(sub_data)

    masked_data["high_hex_entropy"] = "I'm gonna make him an offer he can't refuse."
    masked_sub_data["list_test"] = ["not bad stuff", "bad stuff offer", "more good stuff"]
    masked_sub_data["tuple_test"] = ("not bad stuff", "bad stuff offer")
    masked_sub_data["set_test"] = {"not bad stuff", "bad stuff offer", "more good stuff"}

    event = SubclassedCollectedEvent(data=data, new_field=CollectedEvent(data=sub_data))
    expected = SubclassedCollectedEvent(
        data=masked_data, new_field=CollectedEvent(data=masked_sub_data)
    )
    masked_event_dict = _shannon_process(event.dict(), config)
    masked_event = event.parse_obj(masked_event_dict)
    assert masked_event.data == expected.data
    assert masked_event.new_field.data == expected.new_field.data


def test__shannon_process_with_mask_char(data: dict[str, Any], sub_data: dict[str, Any]) -> None:
    """
    Make sure it catches and replaces correctly with the mask_char.
    """
    config = ShannonMaskProcessConfig(
        plugin="shannon-mask-processor", mask_char="*", alphabet="0123456789abcdef"
    )
    masked_data = copy.deepcopy(data)
    masked_sub_data = copy.deepcopy(sub_data)
    asterisks = "*" * len("000123456789abcdef0123456789abcdefdab")

    masked_data["high_hex_entropy"] = f"I'm gonna make him an {asterisks} he can't refuse."
    masked_sub_data["list_test"] = ["not bad stuff", f"bad stuff {asterisks}", "more good stuff"]
    masked_sub_data["tuple_test"] = ("not bad stuff", f"bad stuff {asterisks}")
    masked_sub_data["set_test"] = {"not bad stuff", f"bad stuff {asterisks}", "more good stuff"}

    event = SubclassedCollectedEvent(data=data, new_field=CollectedEvent(data=sub_data))
    expected = SubclassedCollectedEvent(
        data=masked_data, new_field=CollectedEvent(data=masked_sub_data)
    )
    masked_event_dict = _shannon_process(event.dict(), config)
    masked_event = event.parse_obj(masked_event_dict)
    assert masked_event.data == expected.data
    assert masked_event.new_field.data == expected.new_field.data
