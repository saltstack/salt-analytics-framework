# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
ElasticSearch forwarder.

Requires the elasticsearch-py python library.
"""
from __future__ import annotations

import logging
import pprint
import uuid
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import cast

from pydantic import Field

from saf.models import CollectedEvent
from saf.models import ForwardConfigBase
from saf.models import PipelineRunContext

try:
    from elasticsearch import JsonSerializer
except ImportError:

    class JsonSerializer:  # type: ignore[no-redef]
        """
        Simple class definition in order not to cause errors when elasticsearch fails to import.
        """


log = logging.getLogger(__name__)


class AnalyticsJsonSerializer(JsonSerializer):
    """
    Custom JSON serializer.
    """

    def default(self, data: Any) -> Any:  # noqa: ANN101,ANN401
        """
        Convert the passed data to a type that can be JSON serialized.
        """
        if isinstance(data, set):
            return list(data)
        if isinstance(data, datetime):
            return data.isoformat()
        if isinstance(data, timedelta):
            return data.total_seconds()
        return super().default(data)


class ElasticSearchEvent(CollectedEvent):
    """
    ElasticSearch Event.
    """

    index: str
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # noqa: A003
    data: Dict[str, Any]


class ElasticSearchConfig(ForwardConfigBase):
    """
    Configuration schema for the disk forward plugin.
    """

    hosts: List[str]
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 10
    index: Optional[str] = None


def get_config_schema() -> Type[ElasticSearchConfig]:
    """
    Get the ElasticSearch forwarder configuration schema.
    """
    return ElasticSearchConfig


async def forward(
    *,
    ctx: PipelineRunContext[ElasticSearchConfig],
    event: ElasticSearchEvent | CollectedEvent,
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
        ctx.cache["client"] = client = AsyncElasticsearch(
            hosts=config.hosts,
            serializers={"application/json": AnalyticsJsonSerializer()},
            **optional_config,
        )
        connection_info = await client.info()
        log.warning("ES Connection Info:\n%s", pprint.pformat(connection_info))
    client = ctx.cache["client"]
    if isinstance(event, ElasticSearchEvent):
        es_id = event.id
        es_index = event.index
    else:
        es_id = str(uuid.uuid4())
        if ctx.config.index is None:
            msg = (
                "Event to forward is not an instance of ElasticSearchEvent and the "
                "elasticsearch plugin index configuration is not defined."
            )
            raise RuntimeError(msg)
        es_index = ctx.config.index
    data = cast(Dict[str, Any], event.data).copy()
    if "@timestamp" not in data:
        data["@timestamp"] = event.timestamp
    log.debug(
        "ElasticSearch Forward Details:\nindex: %s\nid: %s\ndata:\n%s",
        es_index,
        es_id,
        pprint.pformat(data),
    )
    ret = await client.index(index=es_index, id=es_id, body=data)
    log.debug(
        "ElasticSearch Forward Response(index: %s; id: %s):\n%s",
        es_index,
        es_id,
        pprint.pformat(ret),
    )
