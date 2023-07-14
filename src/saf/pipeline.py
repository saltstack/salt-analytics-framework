# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Salt Analytics Framework Pipeline.
"""
from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import TYPE_CHECKING
from typing import Any
from typing import AsyncIterator
from typing import TypeVar

import aiostream.stream
import backoff

from saf.models import CollectConfigBase
from saf.models import CollectedEvent
from saf.models import ForwardConfigBase
from saf.models import PipelineConfig
from saf.models import PipelineRunContext
from saf.models import ProcessConfigBase

if TYPE_CHECKING:
    from types import ModuleType

log = logging.getLogger(__name__)


def _check_backoff_exception(exc: Exception) -> bool:
    if isinstance(exc, asyncio.CancelledError):
        return True
    return False


def _log_backoff_exception(details: dict[str, Any]) -> None:
    if details["tries"] == 1:
        # Log the exception on the first time it occurs
        log.exception(details["exception"])


P = TypeVar("P", bound="Pipeline")


class Pipeline:
    """
    Salt Analytics Pipeline.
    """

    def __init__(self: P, name: str, config: PipelineConfig) -> None:
        self.name = name
        self.config = config
        self.collect_configs: list[CollectConfigBase] = []
        for config_name in config.collect:
            self.collect_configs.append(config.parent.collectors[config_name])
        self.process_configs: list[ProcessConfigBase] = []
        for config_name in config.process:
            self.process_configs.append(config.parent.processors[config_name])
        self.forward_configs: list[ForwardConfigBase] = []
        for config_name in config.forward:
            self.forward_configs.append(config.parent.forwarders[config_name])

        self.shared_cache: dict[str, Any] = {}
        self.collect_ctxs: dict[str, PipelineRunContext[CollectConfigBase]] = {}
        self.process_ctxs: dict[str, PipelineRunContext[ProcessConfigBase]] = {}
        self.forward_ctxs: dict[str, PipelineRunContext[ForwardConfigBase]] = {}

    async def run(self: P) -> None:
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
            except Exception:
                log.exception(
                    "Failed to start the pipeline %s due to an error",
                    self.name,
                )
                break
            if self.config.restart is False:
                log.info(
                    "The pipeline %r has the 'restart' config setting set to False. "
                    "Not restarting it.",
                    self.name,
                )
                break

    @backoff.on_exception(
        backoff.expo,
        Exception,
        jitter=backoff.full_jitter,
        max_tries=5,
        giveup=_check_backoff_exception,
        on_backoff=_log_backoff_exception,
    )
    async def _run(self: P) -> None:
        self._build_contexts()
        async for event in self._collectors_stream():
            if self.process_configs:
                async for processed_event in self._pipe_process_events(event):
                    await self._forward_event(processed_event)
            else:
                await self._forward_event(event)

    def _build_contexts(self: P) -> None:
        for collect_config in self.collect_configs:
            if collect_config.name not in self.collect_ctxs:
                self.collect_ctxs[collect_config.name] = PipelineRunContext.model_construct(
                    config=collect_config,
                    shared_cache=self.shared_cache,
                )
        for process_config in self.process_configs:
            if process_config.name not in self.process_ctxs:
                self.process_ctxs[process_config.name] = PipelineRunContext.model_construct(
                    config=process_config,
                    shared_cache=self.shared_cache,
                )
        for forward_config in self.forward_configs:
            if forward_config.name not in self.forward_ctxs:
                self.forward_ctxs[forward_config.name] = PipelineRunContext.model_construct(
                    config=forward_config,
                    shared_cache=self.shared_cache,
                )

    async def _collectors_stream(self: P) -> AsyncIterator[CollectedEvent]:
        collectors = []
        for collect_config in self.collect_configs:
            collect_plugin = collect_config.loaded_plugin
            collectors.append(
                collect_plugin.collect(
                    ctx=self.collect_ctxs[collect_config.name],
                ),
            )
        combined = aiostream.stream.merge(*collectors)
        async with combined.stream() as stream:
            async for event in stream:
                yield event

    async def _pipe_process_event(
        self: P,
        process_config: ProcessConfigBase,
        event: CollectedEvent,
    ) -> AsyncIterator[CollectedEvent]:
        process_plugin = process_config.loaded_plugin
        async for processed_event in process_plugin.process(
            ctx=self.process_ctxs[process_config.name], event=event
        ):
            # Allow other coroutines to run
            await asyncio.sleep(0)
            if processed_event is not None:
                yield processed_event

    async def _pipe_process_events(self: P, event: CollectedEvent) -> AsyncIterator[CollectedEvent]:
        process_configs = list(self.process_configs)
        process_config = process_configs.pop(0)
        process = aiostream.stream.chain(self._pipe_process_event(process_config, event))
        for process_config in process_configs:
            process |= aiostream.pipe.flatmap(partial(self._pipe_process_event, process_config))
        if TYPE_CHECKING:
            assert process
        async with process.stream() as stream:
            async for processed_event in stream:
                # Allow other coroutines to run
                await asyncio.sleep(0)
                if processed_event is not None:
                    yield processed_event

    async def _forward_event(self: P, event: CollectedEvent) -> None:
        # Forward the event
        coros = []
        for forward_config in self.forward_configs:
            forward_plugin = forward_config.loaded_plugin
            coros.append(
                self._wrap_forwarder_plugin_call(
                    forward_plugin,
                    self.forward_ctxs[forward_config.name],
                    # We pass a copy of the event so that any forwarder get's the
                    # same event and is free to modify it at will
                    event.model_copy(),
                ),
            )
        await asyncio.gather(*coros)

    async def _wrap_forwarder_plugin_call(
        self: P,
        plugin: ModuleType,
        ctx: PipelineRunContext[ForwardConfigBase],
        event: CollectedEvent,
    ) -> None:
        try:
            # Allow other coroutines to run
            await asyncio.sleep(0)
            await plugin.forward(ctx=ctx, event=event)
        except Exception:
            log.exception(
                "An exception occurred while forwarding the event through config %r",
                ctx.config,
            )

    def _cleanup(self: P) -> None:
        self.shared_cache.clear()
        self.collect_ctxs.clear()
        self.process_ctxs.clear()
        self.forward_ctxs.clear()

    def __enter__(self: P) -> P:
        """
        Enter pipeline context managert.
        """
        return self

    def __exit__(self: P, *_: Any) -> None:  # noqa: ANN401
        """
        Exit pipeline context managert.
        """
        self._cleanup()
