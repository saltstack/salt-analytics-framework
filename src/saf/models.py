# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Salt Analytics Framework Models.
"""
from __future__ import annotations

import logging
import platform
from datetime import datetime
from datetime import timezone
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union

import salt.utils.network
import salt.version
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import PrivateAttr
from pydantic import field_validator
from pydantic.functional_validators import PlainValidator
from typing_extensions import Annotated

import saf
from saf.plugins import PluginsList
from saf.utils import dt

if TYPE_CHECKING:
    from types import ModuleType

log = logging.getLogger(__name__)


class NonMutableModel(BaseModel):
    """
    Base class for non mutable models.
    """

    model_config = ConfigDict(frozen=True)


NMC = TypeVar("NMC", bound="NonMutableConfig")


class NonMutableConfig(BaseModel):
    """
    Base class for non-mutable configurations.
    """

    _parent: AnalyticsConfig = PrivateAttr()

    model_config = ConfigDict(frozen=True)

    @property
    def parent(self: NMC) -> AnalyticsConfig:
        """
        Return the parent configuration schema.
        """
        return self._parent


PCMI = TypeVar("PCMI", bound="PluginConfigMixin")


class PluginConfigMixin(NonMutableConfig):
    """
    Base class for plugin configuration schemas.
    """

    plugin: str

    _name: str = PrivateAttr()

    @property
    def name(self: PCMI) -> str:
        """
        Return the plugin name as defined in the configuration file.
        """
        return self._name

    @property
    def loaded_plugin(self: PCMI) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        raise NotImplementedError


CCB = TypeVar("CCB", bound="CollectConfigBase")


class CollectConfigBase(PluginConfigMixin):
    """
    Base config schema for collect plugins.
    """

    @property
    def loaded_plugin(self: CCB) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        return PluginsList.instance().collectors[self.plugin]


PCB = TypeVar("PCB", bound="ProcessConfigBase")


class ProcessConfigBase(PluginConfigMixin):
    """
    Base config schema for process plugins.
    """

    @property
    def loaded_plugin(self: PCB) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        return PluginsList.instance().processors[self.plugin]


FCB = TypeVar("FCB", bound="ForwardConfigBase")


class ForwardConfigBase(PluginConfigMixin):
    """
    Base config schema for forward plugins.
    """

    @property
    def loaded_plugin(self: FCB) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        return PluginsList.instance().forwarders[self.plugin]


PC = TypeVar("PC", bound="PipelineConfig")


class PipelineConfig(NonMutableConfig):
    """
    Base config schema for pipeline configuration.
    """

    collect: List[str]
    process: List[str] = Field(default_factory=list)
    forward: List[str]
    enabled: bool = True
    restart: bool = True

    _name: str = PrivateAttr()

    @property
    def name(self: PC) -> str:
        """
        Return the pipeline name as defined in the configuration file.
        """
        return self._name


AC = TypeVar("AC", bound="AnalyticsConfig")


def _instantiate_collector(data: dict[str, Any]) -> CollectConfigBase:
    plugin_cls = CollectConfigBase
    plugin = data["plugin"]
    plugin_module = PluginsList.instance().collectors[plugin]
    try:
        initial_plugin_cls = plugin_module.get_config_schema()
        plugin_cls = initial_plugin_cls.model_rebuild() or initial_plugin_cls
    except AttributeError:
        log.debug(
            "The %r collect plugin does not provide a 'get_config_schema' function, defaulting to %s",
            plugin,
            plugin_cls,
        )

    return plugin_cls.model_validate(data)


CollectConfig = Annotated[CollectConfigBase, PlainValidator(_instantiate_collector)]


def _instantiate_processor(data: dict[str, Any]) -> ProcessConfigBase:
    plugin_cls = ProcessConfigBase
    plugin = data["plugin"]
    plugin_module = PluginsList.instance().processors[plugin]
    try:
        initial_plugin_cls = plugin_module.get_config_schema()
        plugin_cls = initial_plugin_cls.model_rebuild() or initial_plugin_cls
    except AttributeError:
        log.debug(
            "The %r process plugin does not provide a 'get_config_schema' function, defaulting to %s",
            plugin,
            plugin_cls,
        )

    return plugin_cls.model_validate(data)


ProcessConfig = Annotated[ProcessConfigBase, PlainValidator(_instantiate_processor)]


def _instantiate_forwarder(data: dict[str, Any]) -> ForwardConfigBase:
    plugin_cls = ForwardConfigBase
    plugin = data["plugin"]
    plugin_module = PluginsList.instance().forwarders[plugin]
    try:
        initial_plugin_cls = plugin_module.get_config_schema()
        plugin_cls = initial_plugin_cls.model_rebuild() or initial_plugin_cls
    except AttributeError:
        log.debug(
            "The %r forward plugin does not provide a 'get_config_schema' function, defaulting to %s",
            plugin,
            plugin_cls,
        )

    return plugin_cls.model_validate(data)


ForwardConfig = Annotated[ForwardConfigBase, PlainValidator(_instantiate_forwarder)]


class AnalyticsConfig(BaseModel):
    """
    Salt Analytics Framework configuration.
    """

    collectors: Dict[str, CollectConfig]
    processors: Dict[str, ProcessConfig] = Field(default_factory=dict)
    forwarders: Dict[str, ForwardConfig]
    pipelines: Dict[str, PipelineConfig]
    salt_config: Dict[str, Any]

    @field_validator("pipelines", mode="before")
    @classmethod
    def _validate_pipelines(
        cls: Type[AC], pipelines: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        for name, data in pipelines.items():
            collect = data["collect"]
            if isinstance(collect, str):
                collect = [collect]
            process = data.get("process")
            forward = data["forward"]
            if process is None:
                process = []
            elif isinstance(process, str):
                process = [process]
            if isinstance(forward, str):
                forward = [forward]

            pipelines[name]["collect"] = collect
            pipelines[name]["process"] = process
            pipelines[name]["forward"] = forward
            pipelines[name].setdefault("enabled", True)
        return pipelines

    def model_post_init(self: AC, __context: Any) -> None:  # noqa: ANN401
        """
        Set the `_parent` attribute on child schemas.
        """
        super().model_post_init(__context)
        # Allow plugin configurations to access the full configuration, this instance
        for entry in (self.collectors, self.processors, self.forwarders, self.pipelines):
            if entry is None:
                continue
            for name, config in entry.items():  # type: ignore[attr-defined]
                config._name = name  # pylint: disable=protected-access
                config._parent = self  # pylint: disable=protected-access


class CollectedEvent(BaseModel):
    """
    Class representing each of the collected events.
    """

    data: Mapping[str, Any]
    timestamp: Optional[datetime] = Field(default_factory=dt.utcnow)


SE = TypeVar("SE", bound="SaltEvent")


class SaltEvent(NonMutableModel):
    """
    Class representing an event from Salt's event bus.
    """

    tag: str
    stamp: datetime
    data: Dict[str, Any]
    raw_data: Dict[str, Any]

    @staticmethod
    def _convert_stamp(stamp: str) -> datetime:
        _stamp: datetime
        try:
            _stamp = datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc)
        except AttributeError:  # pragma: no cover
            # Python < 3.7
            _stamp = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
        return _stamp

    @field_validator("stamp")
    @classmethod
    def _validate_stamp(cls: Type[SE], value: Union[str, datetime]) -> datetime:
        if isinstance(value, datetime):
            return value
        return SaltEvent._convert_stamp(value)


PipelineRunContextConfigType = TypeVar("PipelineRunContextConfigType", bound=NonMutableConfig)


class RuntimeAnalyticsInfo(NonMutableModel):
    """
    Salt analytics runtime information.
    """

    version: str


class RuntimeSaltInfo(NonMutableModel):
    """
    Salt runtime information.
    """

    id: str  # noqa: A003
    role: str
    version: str
    version_info: Tuple[int, ...]


class RuntimeInfo(NonMutableModel):
    """
    Salt analytics pipelines runtime information.
    """

    salt: RuntimeSaltInfo
    analytics: RuntimeAnalyticsInfo


class PipelineRunContext(NonMutableModel, Generic[PipelineRunContextConfigType]):
    """
    Class representing a pipeline run context.
    """

    config: PipelineRunContextConfigType
    cache: Dict[str, Any] = Field(default_factory=dict)
    shared_cache: Dict[str, Any] = Field(default_factory=dict)
    _info: Optional[RuntimeInfo] = PrivateAttr(default=None)

    @property
    def pipeline_config(self) -> AnalyticsConfig:  # noqa: ANN101
        """
        Return the analytics configuration.
        """
        return self.config.parent

    @property
    def salt_config(self) -> Dict[str, Any]:  # noqa: ANN101
        """
        Return the salt configuration.
        """
        config: Dict[str, Any] = self.config.parent.salt_config
        return config

    @property
    def info(self) -> RuntimeInfo:  # noqa: ANN101
        """
        Return the pipeline runtime information.
        """
        if self._info is None:
            salt_config = self.salt_config
            salt_id = salt_config.get("id")
            if salt_id is None:
                salt_id = salt_config.get("grains", {}).get("fqdn")
            if salt_id is None:
                salt_id = salt.utils.network.get_fqhostname()
            if salt_id is None:
                salt_id = platform.node()
            self._info = RuntimeInfo.model_construct(
                salt=RuntimeSaltInfo.model_construct(
                    id=salt_id,
                    role=salt_config["__role"],
                    version=salt.version.__version__,
                    version_info=salt.version.__saltstack_version__.info,
                ),
                analytics=RuntimeAnalyticsInfo.model_construct(
                    version=saf.__version__,
                ),
            )
        return self._info
