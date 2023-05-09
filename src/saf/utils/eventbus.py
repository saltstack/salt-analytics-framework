# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Wrapper functions around Salt's eventbus.
"""
from __future__ import annotations

import asyncio
import copy
import fnmatch
import logging
import queue
from typing import TYPE_CHECKING
from typing import Any
from typing import AsyncIterator

import salt.utils.event

from saf.models import SaltEvent

if TYPE_CHECKING:
    from queue import Queue

log = logging.getLogger(__name__)


def _construct_event(event_data: dict[str, Any]) -> SaltEvent | None:
    """
    Construct a :py:class:`~saf.models.SaltEvent` from a salt event payload.
    """
    salt_event = None
    try:
        event_raw_data = copy.deepcopy(event_data)
        # Salt's event data has some "private" keys, for example, "_stamp".
        # We'll just store a full_data attribute and clean up the regular data of these keys
        for key in list(event_data):
            if key.startswith("_"):
                event_data.pop(key)
        salt_event = SaltEvent(
            tag=event_data["tag"],
            stamp=event_raw_data["_stamp"],
            data=event_data["data"],
            raw_data=event_raw_data,
        )
        log.debug("Constructed SaltEvent: %s", salt_event)
    except Exception:
        log.exception("Failed to construct a SaltEvent")
    return salt_event


def _process_events(  # noqa: C901
    opts: dict[str, Any],
    events_queue: Queue[SaltEvent],
    tags: set[str],
) -> None:
    """
    Collect events from Salt's event bus.

    This function is meant to run on a separate threads until Salt stops using tornado or
    it's safe to use asyncio as the asynchronous loop.
    """
    opts["file_client"] = "local"
    with salt.utils.event.get_event(
        opts["__role"],
        sock_dir=opts["sock_dir"],
        transport=opts["transport"],
        opts=opts,
        listen=True,
    ) as eventbus:
        for event in eventbus.iter_events(full=True, auto_reconnect=True):
            if not event:
                continue
            event_tag = event["tag"]
            event_data = event["data"]
            if event_tag == "__beacons_return":
                # Special case __beacons_return event since it's basically a container
                # for all of the Salt's beacon events on each beacons collect iteration

                for beacon_event_data in event_data["beacons"]:
                    for tag in tags:
                        try:
                            if fnmatch.fnmatch(beacon_event_data["tag"], tag):
                                if "_stamp" not in beacon_event_data:
                                    # Wrapped beacon data usually lack the _stamp key/value pair. Use parent's.
                                    beacon_event_data["_stamp"] = event_data["_stamp"]
                                # Unwrap the nested data key/value pair if needed
                                if "data" in beacon_event_data["data"]:
                                    beacon_event_data["data"] = beacon_event_data["data"].pop(
                                        "data"
                                    )
                                log.debug(
                                    "Matching Beacon event; TAG: %r DATA: %r",
                                    beacon_event_data["tag"],
                                    beacon_event_data["data"],
                                )
                                salt_event = _construct_event(beacon_event_data)
                                if salt_event:
                                    events_queue.put_nowait(salt_event)
                                # We found a matching tag, stop iterating tags
                                break
                        except Exception:
                            log.exception(
                                "Ran into an error while processing beacon events",
                            )
                # No additional processing required, process to next event from the event bus
                continue

            # Non special cased salt event tags
            for tag in tags:
                if fnmatch.fnmatch(event_tag, tag):
                    log.debug("Matching event; TAG: %r DATA: %r", event_tag, event_data)
                    salt_event = _construct_event(event_data)
                    if salt_event:
                        events_queue.put_nowait(salt_event)
                    # We found a matching tag, stop iterating tags
                    break


async def _start_event_listener(
    *,
    opts: dict[str, Any],
    events_queue: Queue[SaltEvent],
    tags: set[str],
) -> None:
    # We don't want to mix asyncio and tornado loops,
    # so, we defer the salt event listening to a separate
    # thread.
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        _process_events,
        opts,
        events_queue,
        tags,
    )


async def iter_events(*, tags: set[str], opts: dict[str, Any]) -> AsyncIterator[SaltEvent]:
    """
    Method called to collect events.
    """
    loop = asyncio.get_event_loop()
    events_queue: Queue[SaltEvent] = queue.Queue()
    process_events_task = loop.create_task(
        _start_event_listener(opts=opts, events_queue=events_queue, tags=tags)
    )
    try:
        while True:
            try:
                event = events_queue.get_nowait()
                yield event
            except queue.Empty:
                await asyncio.sleep(0.1)
    finally:
        process_events_task.cancel()
