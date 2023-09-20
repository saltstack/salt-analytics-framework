# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Convert beacon event to an elastic search index event.
"""
from __future__ import annotations

import json
import logging
import pprint
from typing import TYPE_CHECKING
from typing import AsyncIterator
from typing import Type

from saf.forward.elasticsearch import ElasticSearchEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

if TYPE_CHECKING:
    from saf.process.job_aggregate import JobAggregateCollectedEvent

log = logging.getLogger(__name__)


class SaltStateJobsToESConfig(ProcessConfigBase):
    """
    Processor configuration.
    """


def get_config_schema() -> Type[SaltStateJobsToESConfig]:
    """
    Get the test collect plugin configuration schema.
    """
    return SaltStateJobsToESConfig


async def process(
    *,
    ctx: PipelineRunContext[SaltStateJobsToESConfig],  # noqa: ARG001
    event: JobAggregateCollectedEvent,
) -> AsyncIterator[ElasticSearchEvent]:
    """
    Method called to collect events, in this case, generate.
    """
    data = event.dict()
    data.pop("data", None)
    data.update(event.data)
    data["state_name"] = data["fun_args"][0]
    # Some field must be cast to JSON strings or EL will complain about
    # different types
    for key in ("fun_args", "return"):
        if key in data:
            data[key] = json.dumps(data[key])
    data["@timestamp"] = event.start_time
    evt = ElasticSearchEvent.construct(index="salt_state_runs", data=data)
    log.debug("ElasticSearchEvent: %s", pprint.pformat(evt.dict()))
    yield evt
