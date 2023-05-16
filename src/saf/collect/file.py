# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
A file collector plugin.
"""
from __future__ import annotations

import asyncio
import logging
import os
import typing
from typing import AsyncIterator
from typing import Type

if typing.TYPE_CHECKING:
    import pathlib

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class FileCollectConfig(CollectConfigBase):
    """
    Configuration schema for the file collect plugin.
    """

    path: pathlib.Path
    # If true, starts at the beginning of a file, else at the end
    backfill: bool = False
    wait: float = 5
    # If true, reads to the end of the file, else one line at a time
    multiline: bool = False
    file_mode: str = "r"


def get_config_schema() -> Type[FileCollectConfig]:
    """
    Get the file collect plugin configuration schema.
    """
    return FileCollectConfig


async def collect(*, ctx: PipelineRunContext[FileCollectConfig]) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect file contents.
    """
    config = ctx.config
    try:
        with config.path.open(mode=config.file_mode) as rfh:
            # If we do not need to gather older content, we put the cursor at the end of file
            if not config.backfill:
                rfh.seek(0, os.SEEK_END)
            while True:
                if config.multiline:
                    contents = rfh.readlines()
                else:
                    contents = rfh.readline()
                if not contents:
                    await asyncio.sleep(config.wait)
                else:
                    event = CollectedEvent(data={"lines": contents})
                    yield event

    except FileNotFoundError as exc:
        log.debug("File %s not found", exc.filename)
