# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier:  Apache-2.0
"""
Salt Analytics Framework Pipelines Manager.
"""
import asyncio
import logging
from asyncio import Task
from typing import Dict
from typing import Optional

import aiorun

from saf.models import AnalyticsConfig
from saf.pipeline import Pipeline

log = logging.getLogger(__name__)


class Manager:
    """
    Pipelines Manager.
    """

    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.pipelines: Dict[str, Pipeline] = {}
        for name, pipeline_config in config.pipelines.items():
            self.pipelines[name] = Pipeline(name, pipeline_config)
        self.pipeline_tasks: Dict[str, Task] = {}  # type: ignore[type-arg]
        self.loop = asyncio.get_event_loop()

    async def run(self) -> None:
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

    async def await_stopped(self) -> None:
        """
        Wait until all pipelines have been stopped.
        """
        await self.stop_pipelines()

    async def start_pipelines(self) -> None:
        """
        Start the pipelines.
        """
        for name in self.pipelines:
            result = await self.start_pipeline(name)
            if result is not None:
                log.warning(result)

    async def stop_pipelines(self) -> None:
        """
        Stop the pipelines.
        """
        for name in list(self.pipeline_tasks):
            result = await self.stop_pipeline(name)
            if result is not None:
                log.warning(result)

    async def start_pipeline(self, name: str) -> Optional[str]:
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

    async def stop_pipeline(self, name: str) -> Optional[str]:
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
