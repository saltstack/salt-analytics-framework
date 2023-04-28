# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from __future__ import annotations

import copy
from typing import Any

import pytest

from saf.models import CollectedEvent
from saf.process.regex_mask import _regex_process
from saf.process.regex_mask import RegexMaskProcessConfig


class SubclassedCollectedEvent(CollectedEvent):
    """
    A subclass of CollectedEvent to allow recursive testing of regex masker.
    """

    new_field: CollectedEvent


@pytest.fixture
def base_rules() -> dict[str, Any]:
    # No, this is not a good regex for real IP matching
    rules = {
        "SECRET": "KEY::[0-9]{10}",
        "IP": "[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}",
    }
    return rules


@pytest.fixture
def data() -> dict[str, Any]:
    data = {
        "secret_key": "This is my secret key KEY::1234567890. Nice.",
        "nothing": "",
        "no_repl": "Nothing will be replaced in here.",
        "list_test": ["not bad stuff", "bad stuff KEY::0987654321", "more good stuff"],
        "tuple_test": ("not bad stuff", "bad stuff KEY::0987654321"),
        "set_test": {"not bad stuff", "bad stuff KEY::0987654321", "more good stuff"},
    }
    return data


@pytest.fixture
def sub_data() -> dict[str, Any]:
    sub_data = {
        "ip_address": "My IP is 127.0.0.1",
        "integer": 12,
    }
    return sub_data


def test__regex_process(
    base_rules: dict[str, Any], data: dict[str, Any], sub_data: dict[str, Any]
) -> None:
    """
    Make sure it catches and replaces correctly with the mask_str.
    """
    config = RegexMaskProcessConfig(plugin="regex-mask-processor", rules=base_rules)
    masked_data = copy.deepcopy(data)
    masked_sub_data = copy.deepcopy(sub_data)

    masked_data["secret_key"] = "This is my secret key <:SECRET:>. Nice."
    masked_data["list_test"] = ["not bad stuff", "bad stuff <:SECRET:>", "more good stuff"]
    masked_data["tuple_test"] = ("not bad stuff", "bad stuff <:SECRET:>")
    masked_data["set_test"] = {"not bad stuff", "bad stuff <:SECRET:>", "more good stuff"}
    masked_sub_data["ip_address"] = "My IP is <:IP:>"

    event = SubclassedCollectedEvent(data=data, new_field=CollectedEvent(data=sub_data))
    expected = SubclassedCollectedEvent(
        data=masked_data, new_field=CollectedEvent(data=masked_sub_data)
    )
    masked_event_dict = _regex_process(event.dict(), config)
    masked_event = event.parse_obj(masked_event_dict)
    assert masked_event.data == expected.data
    assert masked_event.new_field.data == expected.new_field.data


def test__regex_process_with_mask_char(
    base_rules: dict[str, Any], data: dict[str, Any], sub_data: dict[str, Any]
) -> None:
    """
    Make sure it catches and replaces correctly with the mask_char.
    """
    config = RegexMaskProcessConfig(plugin="regex-mask-processor", rules=base_rules, mask_char="*")
    masked_data = copy.deepcopy(data)
    masked_sub_data = copy.deepcopy(sub_data)

    masked_data["secret_key"] = "This is my secret key ***************. Nice."
    masked_data["list_test"] = ["not bad stuff", "bad stuff ***************", "more good stuff"]
    masked_data["tuple_test"] = ("not bad stuff", "bad stuff ***************")
    masked_data["set_test"] = {"not bad stuff", "bad stuff ***************", "more good stuff"}
    masked_sub_data["ip_address"] = "My IP is *********"

    event = SubclassedCollectedEvent(data=data, new_field=CollectedEvent(data=sub_data))
    expected = SubclassedCollectedEvent(
        data=masked_data, new_field=CollectedEvent(data=masked_sub_data)
    )
    masked_event_dict = _regex_process(event.dict(), config)
    masked_event = event.parse_obj(masked_event_dict)
    assert masked_event.data == expected.data
    assert masked_event.new_field.data == expected.new_field.data
