# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Convert beacon event to an elastic search index event.
"""
from __future__ import annotations

import logging
import pprint
from typing import TYPE_CHECKING
from typing import Any
from typing import AsyncIterator
from typing import Type
from typing import cast

from saf.forward.elasticsearch import ElasticSearchEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

if TYPE_CHECKING:
    from saf.collect.beacons import BeaconCollectedEvent
log = logging.getLogger(__name__)


class BeaconToESConfig(ProcessConfigBase):
    """
    Processor configuration.
    """


def get_config_schema() -> Type[BeaconToESConfig]:
    """
    Get the test collect plugin configuration schema.
    """
    return BeaconToESConfig


async def process(
    *,
    ctx: PipelineRunContext[BeaconToESConfig],
    event: BeaconCollectedEvent,
) -> AsyncIterator[ElasticSearchEvent]:
    """
    Method called to collect events, in this case, generate.
    """
    data = cast(dict[str, Any], event.data).copy()
    data["role"] = ctx.info.salt.role
    evt = ElasticSearchEvent.construct(index=event.beacon, data=data)
    log.debug("ElasticSearchEvent: %s", pprint.pformat(evt.dict()))
    yield evt
