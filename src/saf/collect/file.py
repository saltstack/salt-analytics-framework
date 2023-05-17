# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
A file collector plugin.
"""
from __future__ import annotations

import logging
import os
import pathlib  # noqa: TCH003
from contextlib import ExitStack
from typing import IO
from typing import Any
from typing import AsyncIterator
from typing import List
from typing import Type
from typing import Union

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class FileCollectConfig(CollectConfigBase):
    """
    Configuration schema for the file collect plugin.
    """

    paths: List[pathlib.Path]
    # If true, starts at the beginning of a file, else at the end
    backfill: bool = False
    # If true, reads to the end of the file, else one line at a time
    multiline: bool = False
    file_mode: str = "r"


def get_config_schema() -> Type[FileCollectConfig]:
    """
    Get the file collect plugin configuration schema.
    """
    return FileCollectConfig


def _process_file(file_handle: IO[str], config: FileCollectConfig) -> Union[CollectedEvent, None]:
    event = None
    contents: Any
    if config.multiline:
        contents = file_handle.readlines()
    else:
        contents = file_handle.readline()
    if contents:
        event = CollectedEvent(data={"lines": contents})

    return event


async def collect(*, ctx: PipelineRunContext[FileCollectConfig]) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect file contents.
    """
    config = ctx.config

    with ExitStack() as stack:
        try:
            handles = [
                stack.enter_context(path.open(mode=config.file_mode)) for path in config.paths
            ]
            if not config.backfill:
                for handle in handles:
                    handle.seek(0, os.SEEK_END)
            while True:
                for rfh in handles:
                    contents = _process_file(rfh, config)
                    if contents is not None:
                        yield CollectedEvent(data={"lines": contents})
        except FileNotFoundError as exc:
            log.debug("File %s not found", exc.filename)
