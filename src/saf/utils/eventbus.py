# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Wrapper functions around Salt's eventbus.
"""
import asyncio
import copy
import fnmatch
import logging
import queue
from queue import Queue
from typing import Any
from typing import AsyncIterator
from typing import Dict
from typing import Set

import salt.utils.event

from saf.models import SaltEvent

log = logging.getLogger(__name__)


def _process_events(
    opts: Dict[str, Any],
    events_queue: Queue[SaltEvent],
    tags: Set[str],
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
            for tag in tags:
                if fnmatch.fnmatch(event_tag, tag):
                    log.debug("Matching event; TAG: %r DATA: %r", event_tag, event_data)
                    event_raw_data = copy.deepcopy(event_data)
                    # Salt's event data has some "private" keys, for example, "_stamp".
                    # We'll just store a full_data attribute and clean up the regular data of these keys
                    for key in list(event_data):
                        if key.startswith("_"):
                            event_data.pop(key)
                    events_queue.put_nowait(
                        SaltEvent(
                            tag=event_tag,
                            stamp=event_raw_data["stamp"],
                            data=event_data,
                            raw_data=event_raw_data,
                        )
                    )


async def _start_event_listener(
    *,
    opts: Dict[str, Any],
    events_queue: Queue[SaltEvent],
    tags: Set[str],
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


async def iter_events(*, tags: Set[str], opts: Dict[str, Any]) -> AsyncIterator[SaltEvent]:
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
