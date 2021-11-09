# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
The beacons collect plugin exists as an implementation example.

It listens to Salt's event bus for beacon events and generates
anaylitics events based off of those.
"""
import logging
from datetime import datetime
from typing import Any
from typing import AsyncIterator
from typing import Dict
from typing import List
from typing import Type
from typing import Union

from pydantic import validator

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import SaltEvent
from saf.utils import eventbus

log = logging.getLogger(__name__)


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
    tag: str
    stamp: datetime
    raw_data: Dict[str, Any]

    @staticmethod
    def _convert_stamp(stamp: str) -> datetime:
        _stamp: datetime
        try:
            _stamp = datetime.fromisoformat(stamp)
        except AttributeError:  # pragma: no cover
            # Python < 3.7
            _stamp = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%S.%f")
        return _stamp

    @validator("stamp")
    def _validate_stamp(cls, value: Union[str, datetime]) -> datetime:
        if isinstance(value, datetime):
            return value
        return BeaconCollectedEvent._convert_stamp(value)


def get_config_schema() -> Type[BeaconsConfig]:
    """
    Get the beacons plugin configuration schema.
    """
    return BeaconsConfig


async def collect(*, config: BeaconsConfig) -> AsyncIterator[BeaconCollectedEvent]:
    """
    Method called to collect events.
    """
    salt_event: SaltEvent
    tags = {f"salt/beacon/*/{beacon}/*" for beacon in config.beacons}
    log.info("The beacons collect plugin is configured to listen to tags: %s", tags)
    async for salt_event in eventbus.iter_events(opts=config.parent.salt_config.copy(), tags=tags):
        yield BeaconCollectedEvent(
            beacon=salt_event.raw_data["beacon_name"],
            tag=salt_event.tag,
            stamp=salt_event.stamp,
            data=salt_event.data,
            raw_data=salt_event.raw_data,
        )
