# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Salt Analytics Framework Pipeline.
"""
import asyncio
import logging
from types import ModuleType
from typing import List

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import ForwardConfigBase
from saf.models import PipelineConfig
from saf.models import ProcessConfigBase

log = logging.getLogger(__name__)


class Pipeline:
    """
    Salt Analytics Pipeline.
    """

    def __init__(self, name: str, config: PipelineConfig):
        self.name = name
        self.config = config
        self.collect_config: CollectConfigBase = config.parent.collectors[config.collect]
        self.process_configs: List[ProcessConfigBase] = []
        for config_name in config.process:
            self.process_configs.append(config.parent.processors[config_name])
        self.forward_configs: List[ForwardConfigBase] = []
        for config_name in config.forward:
            self.forward_configs.append(config.parent.forwarders[config_name])

    async def run(self) -> None:
        """
        Run the pipeline.
        """
        log.info("Pipeline %r started", self.name)
        while True:
            try:
                await self._run()
            except asyncio.CancelledError:
                log.info("Pipeline %r canceled", self.name)
                break
            except Exception as exc:  # pylint: disable=broad-except
                log.error(
                    "Restarting pipeline %s due to an error: %s", self.name, exc, exc_info=True
                )

    async def _run(self) -> None:
        collect_plugin = self.collect_config.loaded_plugin
        async for event in collect_plugin.collect(config=self.collect_config):
            # Process the event
            for process_config in self.process_configs:
                # We pass copies of the event so that, in case an exception occurs while
                # the event is being processed, and the event has already been modified,
                # the next processor to run will get an unmodified copy of the event, not
                # the partially processed event
                original_event = event.copy()
                process_plugin = process_config.loaded_plugin
                try:
                    event = await process_plugin.process(
                        config=process_config,
                        event=event,
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    log.error(
                        "An exception occurred while processing the event: %s", exc, exc_info=True
                    )
                    # Restore the original event
                    event = original_event
            # Forward the event
            coros = []
            for forward_config in self.forward_configs:
                forward_plugin = forward_config.loaded_plugin
                coros.append(
                    self._wrap_forwarder_plugin_call(
                        forward_plugin,
                        forward_config,
                        event.copy(),
                    ),
                )
            if self.config.concurrent_forwarders:
                await asyncio.gather(*coros)
            else:
                for coro in coros:
                    await coro

    async def _wrap_forwarder_plugin_call(
        self, plugin: ModuleType, config: ForwardConfigBase, event: CollectedEvent
    ) -> None:
        try:
            await plugin.forward(config=config, event=event)
        except Exception as exc:  # pylint: disable=broad-except
            log.error(
                "An exception occurred while forwarding the event through config %r: %s",
                config,
                exc,
                exc_info=True,
            )
