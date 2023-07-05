# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
ElasticSearch forwarder.

Requires the elasticsearch-py python library.
"""
from __future__ import annotations

import logging
import pprint
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from saf.models import CollectedEvent
from saf.models import ForwardConfigBase
from saf.models import PipelineRunContext

log = logging.getLogger(__name__)


class ElasticSearchEvent(CollectedEvent):
    """
    ElasticSearch Event.
    """

    index: str
    id: str  # noqa: A003
    data: Dict[str, Any]


class ElasticSearchConfig(ForwardConfigBase):
    """
    Configuration schema for the disk forward plugin.
    """

    hosts: List[str]
    #    use_ssl: bool = True
    #    verify_ssl: bool = True
    #    ca_certs: Optional[pathlib.Path] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 10


def get_config_schema() -> Type[ElasticSearchConfig]:
    """
    Get the ElasticSearch forwarder configuration schema.
    """
    return ElasticSearchConfig


async def forward(
    *,
    ctx: PipelineRunContext[ElasticSearchConfig],
    event: ElasticSearchEvent,
) -> None:
    """
    Method called to forward the event.
    """
    from elasticsearch import AsyncElasticsearch

    if "client" not in ctx.cache:
        config = ctx.config
        optional_config = {}
        if config.username and config.password:
            optional_config["http_auth"] = (config.username, config.password)
        #        if config.ca_certs:
        #            optional_config["ca_certs"] = config.ca_certs
        ctx.cache["client"] = client = AsyncElasticsearch(
            hosts=config.hosts,
            # use_ssl=config.use_ssl,
            # verify_ssl=config.verify_ssl,
            **optional_config,
        )
        connection_info = await client.info()
        log.warning("ES Connection Info:\n%s", pprint.pformat(connection_info))
    client = ctx.cache["client"]
    ret = await client.index(index=event.index, id=event.id, body=event.data)
    log.warning("ES SEND:\n%s", pprint.pformat(ret))
