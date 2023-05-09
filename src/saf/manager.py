# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier:  Apache-2.0
"""
Salt Analytics Framework Pipelines Manager.
"""
from __future__ import annotations

import asyncio
import logging
from asyncio import Task
from typing import TYPE_CHECKING
from typing import TypeVar

import aiorun

from saf.pipeline import Pipeline

if TYPE_CHECKING:
    from saf.models import AnalyticsConfig

log = logging.getLogger(__name__)

MN = TypeVar("MN", bound="Manager")


class Manager:
    """
    Pipelines Manager.
    """

    def __init__(self: MN, config: AnalyticsConfig) -> None:
        self.config = config
        self.pipelines: dict[str, Pipeline] = {}
        for name, pipeline_config in config.pipelines.items():
            self.pipelines[name] = Pipeline(name, pipeline_config)
        self.pipeline_tasks: dict[str, Task] = {}  # type: ignore[type-arg]
        self.loop = asyncio.get_event_loop()

    async def run(self: MN) -> None:
        """
        Async entry point to run the pipelines.
        """
        await self.start_pipelines()
        try:
            while True:
                try:
                    await asyncio.sleep(0.05)
                except (KeyboardInterrupt, asyncio.CancelledError):
                    break
        finally:
            await aiorun.shutdown_waits_for(self.stop_pipelines())

    async def await_stopped(self: MN) -> None:
        """
        Wait until all pipelines have been stopped.
        """
        await self.stop_pipelines()

    async def start_pipelines(self: MN) -> None:
        """
        Start the pipelines.
        """
        for name in self.pipelines:
            result = await self.start_pipeline(name)
            if result is not None:
                log.warning(result)

    async def stop_pipelines(self: MN) -> None:
        """
        Stop the pipelines.
        """
        for name in list(self.pipeline_tasks):
            result = await self.stop_pipeline(name)
            if result is not None:
                log.warning(result)

    async def start_pipeline(self: MN, name: str) -> str | None:
        """
        Start a pipeline by name.
        """
        log.info("Starting pipeline %r", name)
        if name not in self.pipelines:
            return f"Cannot start unknown pipeline {name!r}"
        pipeline = self.pipelines[name]
        if pipeline.config.enabled is False:
            return f"Pipeline {name!r} is disabled, skipping start."
        if name in self.pipeline_tasks:
            return f"Pipeline {name!r} is already running"
        self.pipeline_tasks[name] = self.loop.create_task(pipeline.run())
        return None

    async def stop_pipeline(self: MN, name: str) -> str | None:
        """
        Stop a pipeline by name.
        """
        log.info("Stopping pipeline %r", name)
        if name not in self.pipeline_tasks:
            return f"Pipeline {name!r} is not running. Not stopping it."
        task = self.pipeline_tasks.pop(name)
        if task.done() is not True:
            task.cancel()
            await task
        return None
