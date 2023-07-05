# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The beacons collect plugin exists as an implementation example.

It listens to Salt's event bus for beacon events and generates
analytics events based off of those.
"""
from __future__ import annotations

import logging
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import AsyncIterator
from typing import Dict
from typing import List
from typing import Type
from typing import TypeVar
from typing import Union

from pydantic import field_validator

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import SaltEvent
from saf.utils import eventbus

log = logging.getLogger(__name__)

BCE = TypeVar("BCE", bound="BeaconCollectedEvent")


class BeaconsConfig(CollectConfigBase):
    """
    Configuration schema for the beacons collect plugin.
    """

    beacons: List[str]


class BeaconCollectedEvent(CollectedEvent):
    """
    Beacons collected event.
    """

    beacon: str
    id: str  # noqa: A003
    tag: str
    stamp: datetime
    raw_data: Dict[str, Any]

    @staticmethod
    def _convert_stamp(stamp: str) -> datetime:
        _stamp: datetime
        try:
            _stamp = datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc)
        except AttributeError:  # pragma: no cover
            # Python < 3.7
            _stamp = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
        return _stamp

    @field_validator("stamp")
    @classmethod
    def _validate_stamp(cls: Type[BCE], value: Union[str, datetime]) -> datetime:
        if isinstance(value, datetime):
            return value
        return BeaconCollectedEvent._convert_stamp(value)


def get_config_schema() -> Type[BeaconsConfig]:
    """
    Get the beacons plugin configuration schema.
    """
    return BeaconsConfig


async def collect(*, ctx: PipelineRunContext[BeaconsConfig]) -> AsyncIterator[BeaconCollectedEvent]:
    """
    Method called to collect events.
    """
    config = ctx.config
    salt_event: SaltEvent
    tags = {f"salt/beacon/*/{beacon}/*" for beacon in config.beacons}
    log.info("The beacons collect plugin is configured to listen to tags: %s", tags)
    async for salt_event in eventbus.iter_events(opts=ctx.salt_config.copy(), tags=tags):
        if "beacon_name" not in salt_event.raw_data:
            # TODO @s0undt3ch: We're listening master side, and the payload is not the same... Fix it?
            continue
        daemon_id = salt_event.data.get("id")
        if daemon_id is None:
            tag_parts = salt_event.tag.split("/")
            daemon_id = tag_parts[2]
        yield BeaconCollectedEvent(
            beacon=salt_event.raw_data["beacon_name"],
            id=daemon_id,
            tag=salt_event.tag,
            stamp=salt_event.stamp,
            data=salt_event.data,
            raw_data=salt_event.raw_data,
        )
