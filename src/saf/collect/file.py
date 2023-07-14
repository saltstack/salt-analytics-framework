# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
A file collector plugin.
"""
from __future__ import annotations

import asyncio
import glob
import logging
import os
import pathlib
import sys
from typing import AsyncIterator
from typing import List
from typing import Type

import aiofiles
import aiostream.stream

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

if sys.version_info < (3, 12):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict  # type: ignore[attr-defined,no-redef]

log = logging.getLogger(__name__)


class CollectedLineData(TypedDict):
    """
    Collected event line data definition.
    """

    line: str
    source: pathlib.Path


class CollectedLineEvent(CollectedEvent):
    """
    Collected line event definition.
    """

    data: CollectedLineData
    backfill: bool = False


class FileCollectConfig(CollectConfigBase):
    """
    Configuration schema for the file collect plugin.
    """

    paths: List[pathlib.Path]
    # If true, starts at the beginning of a file, else at the end
    backfill: bool = False


def get_config_schema() -> Type[FileCollectConfig]:
    """
    Get the file collect plugin configuration schema.
    """
    return FileCollectConfig


async def _process_file(
    *, path: pathlib.Path, backfill: bool = False
) -> AsyncIterator[CollectedLineEvent]:
    """
    Process the given file and `yield` an even per read line.
    """
    async with aiofiles.open(path) as rfh:
        if backfill:
            async for line in rfh:
                yield CollectedLineEvent(
                    data=CollectedLineData(line=line, source=path), backfill=True
                )
        else:
            await rfh.seek(0, os.SEEK_END)
        while True:
            line = await rfh.readline()
            if not line:
                await asyncio.sleep(0.5)
                continue
            yield CollectedLineEvent(data=CollectedLineData(line=line, source=path))


async def collect(
    *, ctx: PipelineRunContext[FileCollectConfig]
) -> AsyncIterator[CollectedLineEvent]:
    """
    Method called to collect file contents.
    """
    config = ctx.config
    streams = []
    for entry in config.paths:
        glob_matches = glob.glob(str(entry))
        if not glob_matches:
            log.error(
                "The glob matching for provided path '%s' did not return any results. Ignoring.",
                entry,
            )
            continue
        for match in glob_matches:
            path = pathlib.Path(match)
            if not path.is_file():
                log.error(
                    "The provided path '%s' does not exist or is not a file. Ignoring.",
                    path,
                )
                continue
        streams.append(_process_file(path=path, backfill=config.backfill))
    combined = aiostream.stream.merge(*streams)
    async with combined.stream() as stream:
        async for event in stream:
            yield event
