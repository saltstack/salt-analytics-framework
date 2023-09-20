# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Aggregate the necessary job info into one event to be forwarded.
"""
from __future__ import annotations

import fnmatch
import logging
import pprint
from typing import TYPE_CHECKING
from typing import AsyncIterator
from typing import Dict
from typing import Set
from typing import Type

from pydantic import Field

from saf.collect.event_bus import EventBusCollectedEvent
from saf.collect.grains import GrainsCollectedEvent
from saf.models import CollectedEvent
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

if TYPE_CHECKING:
    from datetime import datetime
    from datetime import timedelta

log = logging.getLogger(__name__)


class JobAggregateConfig(ProcessConfigBase):
    """
    Job aggregate collector configuration.
    """

    jobs: Set[str] = Field(default_factory=lambda: {"*"})


def get_config_schema() -> Type[JobAggregateConfig]:
    """
    Get the job aggregate collect plugin configuration schema.
    """
    return JobAggregateConfig


class JobAggregateCollectedEvent(CollectedEvent):
    """
    A collected event with aggregated job run information.
    """

    start_time: datetime
    end_time: datetime
    duration: timedelta
    minion_id: str
    grains: Dict[str, str]


async def process(
    *,
    ctx: PipelineRunContext[JobAggregateConfig],
    event: EventBusCollectedEvent | GrainsCollectedEvent,
) -> AsyncIterator[CollectedEvent]:
    """
    Aggregate received events, otherwise store in cache.
    """
    if "watched_jids" not in ctx.cache:
        ctx.cache["watched_jids"] = {}
    if "waiting_for_grains" not in ctx.cache:
        ctx.cache["waiting_for_grains"] = {}
    if isinstance(event, EventBusCollectedEvent):
        log.debug("Event Bus Collected Event:\n%s", pprint.pformat(event.dict()))
        salt_event = event.salt_event
        log.debug("Event Bus Collected Salt Event:\n%s", pprint.pformat(salt_event))
        tag = salt_event.tag
        data = salt_event.data
        if fnmatch.fnmatch(tag, "salt/job/*/new"):
            jid = tag.split("/")[2]
            # We will probably want to make this condition configurable
            salt_func = data.get("fun", "")
            for func_filter in ctx.config.jobs:
                if fnmatch.fnmatch(salt_func, func_filter):
                    log.debug(
                        "The job with JID %r and func %r matched function filter %r",
                        jid,
                        salt_func,
                        func_filter,
                    )
                    if jid not in ctx.cache["watched_jids"]:
                        ctx.cache["watched_jids"][jid] = {
                            "minions": set(data["minions"]),
                            "event": salt_event,
                        }
                    break
        elif fnmatch.fnmatch(tag, "salt/job/*/ret/*"):
            split_tag = tag.split("/")
            jid = split_tag[2]
            minion_id = split_tag[-1]
            if jid in ctx.cache["watched_jids"]:
                ctx.cache["watched_jids"][jid]["minions"].remove(minion_id)
                if not ctx.cache["watched_jids"][jid]["minions"]:
                    # No more minions should return. Remove jid from cache
                    job_start_event = ctx.cache["watched_jids"].pop(jid)["event"]
                else:
                    job_start_event = ctx.cache["watched_jids"][jid]["event"]
                start_time = job_start_event.stamp
                end_time = salt_event.stamp
                duration = end_time - start_time
                grains = ctx.cache.get("grains", {}).get(minion_id, {})
                ret = JobAggregateCollectedEvent.construct(
                    data=data,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    minion_id=minion_id,
                    grains=grains,
                )
                if grains:
                    yield ret
                else:
                    if minion_id not in ctx.cache["waiting_for_grains"]:
                        ctx.cache["waiting_for_grains"][minion_id] = []
                    ctx.cache["waiting_for_grains"][minion_id].append(ret)
            else:
                log.debug(
                    "The JID %r was not found in the 'watched_jids' processor cache. Ignoring", jid
                )
    elif isinstance(event, GrainsCollectedEvent):
        if "grains" not in ctx.cache:
            ctx.cache["grains"] = {}
        ctx.cache["grains"][event.minion] = event.grains
        waiting_events = ctx.cache["waiting_for_grains"].pop(event.minion, ())
        for event_with_grains in waiting_events:
            event_with_grains.grains = event.grains
            yield event_with_grains
