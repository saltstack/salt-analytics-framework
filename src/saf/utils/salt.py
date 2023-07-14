# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""
AsyncIO implementations of some of Salt's classes.
"""
from __future__ import annotations

import asyncio
from functools import partial
from typing import Any

import salt.client
import salt.minion


class MasterClient:
    """
    Naive AsyncIO wrapper around Salt's LocalClient.
    """

    def __init__(self, master_opts: dict[str, Any]) -> None:
        self._opts = master_opts
        if self._opts["__role"] != "master":
            msg = "The options dictionary passed to MasterClient does not look like salt-master options."
            raise RuntimeError(msg)
        self._client = salt.client.LocalClient(mopts=self._opts.copy())

    async def cmd(
        self,
        tgt: str,
        fun: str,
        arg: tuple[Any, ...] | list[Any] = (),
        timeout: int | None = None,
        tgt_type: str = "glob",
        ret: str = "",
        jid: str = "",
        full_return: bool = False,
        kwarg: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str | dict[str, Any]:
        """
        Run a salt command.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self._client.cmd,
                tgt=tgt,
                fun=fun,
                arg=arg,
                timeout=timeout,
                tgt_type=tgt_type,
                ret=ret,
                jid=jid,
                full_return=full_return,
                kwarg=kwarg,
                **kwargs,
            ),
        )


class MinionClient:
    """
    Naive AsyncIO wrapper around Salt's minion execution modules.
    """

    def __init__(self, minion_opts: dict[str, Any]) -> None:
        self._opts = minion_opts.copy()
        self._opts["file_client"] = "local"
        self._client = salt.minion.SMinion(self._opts)

    async def cmd(self, func: str, *args: Any, **kwargs: Any) -> Any:
        """
        Run a salt command.
        """
        if func not in self._client.functions:
            msg = f"The function {func!r} was not found, or could not be loaded."
            raise RuntimeError(msg)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, partial(self._client.functions[func], *args, **kwargs)
        )
