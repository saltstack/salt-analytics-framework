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
from typing import Any
from typing import AsyncIterator
from typing import List
from typing import Type

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


async def collect(*, ctx: PipelineRunContext[FileCollectConfig]) -> AsyncIterator[CollectedEvent]:
    """
    Method called to collect file contents.
    """
    config = ctx.config

    with ExitStack() as stack:
        try:
            handles = {
                str(path): stack.enter_context(path.open(mode=config.file_mode))
                for path in config.paths
            }
            if not config.backfill:
                for handle in handles.values():
                    handle.seek(0, os.SEEK_END)
            while True:
                for path, rfh in handles.items():
                    contents: Any
                    if config.multiline:
                        contents = rfh.readlines()
                    else:
                        contents = rfh.readline()
                    if contents and isinstance(contents, str):
                        contents = [contents]
                    if contents is not None:
                        for line in contents:
                            yield CollectedEvent(data={"lines": line, "source": path})
        except FileNotFoundError as exc:
            log.debug("File %s not found", exc.filename)
