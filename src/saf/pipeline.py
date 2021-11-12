# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Salt Analytics Framework Pipeline.
"""
import asyncio
import logging
from typing import List

from saf.models import CollectConfigBase
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
            except Exception as exc:
                log.error(
                    "Restarting pipeline %s due to an error: %s", self.name, exc, exc_info=True
                )

    async def _run(self) -> None:
        collect_plugin = self.collect_config.loaded_plugin
        async for event in collect_plugin.collect(config=self.collect_config):  # type: ignore[attr-defined]
            # Process the event
            for process_config in self.process_configs:
                # We pass copies of the event so that, in case an exception occurs while
                # the event is being processed, and the event has already been modified,
                # the next processor to run will get an unmodified copy of the event, not
                # the partially processed event
                original_event = event.copy()
                process_plugin = process_config.loaded_plugin
                try:
                    event = await process_plugin.process(  # type: ignore[attr-defined]
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
            for forward_config in self.forward_configs:
                forward_plugin = forward_config.loaded_plugin
                try:
                    await forward_plugin.forward(  # type: ignore[attr-defined]
                        config=forward_config,
                        event=event.copy(),
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    log.error(
                        "An exception occurred while forwarding the event through config %r: %s",
                        forward_config,
                        exc,
                        exc_info=True,
                    )
