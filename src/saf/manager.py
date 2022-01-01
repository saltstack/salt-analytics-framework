# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier:  Apache-2.0
"""
Salt Analytics Framework Pipelines Manager.
"""
import asyncio
import logging
from asyncio import Task
from typing import Dict

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
        self.pipelines = {}
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
            await self.start_pipeline(name)

    async def stop_pipelines(self) -> None:
        """
        Stop the pipelines.
        """
        for name in list(self.pipeline_tasks):
            await self.stop_pipeline(name)

    async def start_pipeline(self, name: str) -> None:
        """
        Start a pipeline by name.
        """
        log.info("Starting pipeline %r", name)
        self.pipeline_tasks[name] = self.loop.create_task(self.pipelines[name].run())

    async def stop_pipeline(self, name: str) -> None:
        """
        Stop a pipeline by name.
        """
        log.info("Stopping pipeline %r", name)
        task = self.pipeline_tasks[name]
        task.cancel()
        await task
        self.pipeline_tasks.pop(name)
