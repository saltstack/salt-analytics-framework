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
from pydantic import Field
from pydantic import PrivateAttr
from pydantic import validator
from pydantic.generics import GenericModel

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

    class Config:
        allow_mutation = False


NMC = TypeVar("NMC", bound="NonMutableConfig")


class NonMutableConfig(BaseModel):
    """
    Base class for non-mutable configurations.
    """

    _parent: AnalyticsConfig = PrivateAttr()

    @property
    def parent(self: NMC) -> AnalyticsConfig:
        """
        Return the parent configuration schema.
        """
        return self._parent

    class Config:
        allow_mutation = False
        underscore_attrs_are_private = True


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

    def __new__(
        cls: Type[CCB],
        plugin: str,
        **kwargs: Dict[str, Any],
    ) -> CollectConfigBase:
        """
        Swap the ``cls`` to instantiate if necessary.

        If the targeted plugin provides a ``get_config_schema`` function, then this
        class instance will use that class instead of the default one
        """
        try:
            plugin_module = PluginsList.instance().collectors[plugin]
            try:
                get_schema_func = plugin_module.get_config_schema
                cls = get_schema_func()  # pylint: disable=self-cls-assignment
            except AttributeError:
                log.debug(
                    "The %r collect plugin does not provide a 'get_config_schema' function, defaulting to %s",
                    plugin,
                    cls,
                )
        except KeyError:
            pass
        instance: CollectConfigBase = PluginConfigMixin.__new__(cls)
        return instance

    @property
    def loaded_plugin(self: CCB) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        try:
            return PluginsList.instance().collectors[self.plugin]
        except KeyError as exc:
            log.warning(
                "Failed to load %r collector plugin. Available collector plugins: %s",
                self.plugin,
                list(PluginsList.instance().collectors),
            )
            raise exc from None


PCB = TypeVar("PCB", bound="ProcessConfigBase")


class ProcessConfigBase(PluginConfigMixin):
    """
    Base config schema for process plugins.
    """

    def __new__(
        cls: Type[PCB],
        plugin: str,
        **kwargs: Dict[str, Any],
    ) -> ProcessConfigBase:
        """
        Swap the ``cls`` to instantiate if necessary.

        If the targeted plugin provides a ``get_config_schema`` function, then this
        class instance will use that class instead of the default one
        """
        try:
            plugin_module = PluginsList.instance().processors[plugin]
            try:
                get_schema_func = plugin_module.get_config_schema
                cls = get_schema_func()  # pylint: disable=self-cls-assignment
            except AttributeError:
                log.debug(
                    "The %r process plugin does not provide a 'get_config_schema' function, defaulting to %s",
                    plugin,
                    cls,
                )
        except KeyError:
            pass
        instance: ProcessConfigBase = PluginConfigMixin.__new__(cls)
        return instance

    @property
    def loaded_plugin(self: PCB) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        try:
            return PluginsList.instance().processors[self.plugin]
        except KeyError as exc:
            log.warning(
                "Failed to load %r processor plugin. Available processor plugins: %s",
                self.plugin,
                list(PluginsList.instance().processors),
            )
            raise exc from None


FCB = TypeVar("FCB", bound="ForwardConfigBase")


class ForwardConfigBase(PluginConfigMixin):
    """
    Base config schema for forward plugins.
    """

    def __new__(
        cls: Type[FCB],
        plugin: str,
        **kwargs: Dict[str, Any],
    ) -> ForwardConfigBase:
        """
        Swap the ``cls`` to instantiate if necessary.

        If the targeted plugin provides a ``get_config_schema`` function, then this
        class instance will use that class instead of the default one
        """
        try:
            plugin_module = PluginsList.instance().forwarders[plugin]
            try:
                get_schema_func = plugin_module.get_config_schema
                cls = get_schema_func()  # pylint: disable=self-cls-assignment
            except AttributeError:
                log.debug(
                    "The %r forward plugin does not provide a 'get_config_schema' function, defaulting to %s",
                    plugin,
                    cls,
                )
        except KeyError:
            pass
        instance: ForwardConfigBase = PluginConfigMixin.__new__(cls)
        return instance

    @property
    def loaded_plugin(self: FCB) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        try:
            return PluginsList.instance().forwarders[self.plugin]
        except KeyError as exc:
            log.warning(
                "Failed to load %r forwarder plugin. Available forwarder plugins: %s",
                self.plugin,
                list(PluginsList.instance().forwarders),
            )
            raise exc from None


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


class AnalyticsConfig(BaseModel):
    """
    Salt Analytics Framework configuration.
    """

    collectors: Dict[str, CollectConfigBase]
    processors: Dict[str, ProcessConfigBase] = Field(default_factory=dict)
    forwarders: Dict[str, ForwardConfigBase]
    pipelines: Dict[str, PipelineConfig]
    salt_config: Dict[str, Any]

    @validator("pipelines", pre=True)
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

    def _init_private_attributes(self: AC) -> None:
        """
        Set the `_parent` attribute on child schemas.
        """
        super()._init_private_attributes()
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

    @validator("stamp")
    @classmethod
    def _validate_stamp(cls: Type[SE], value: Union[str, datetime]) -> datetime:
        if isinstance(value, datetime):
            return value
        return SaltEvent._convert_stamp(value)


PipelineRunContextConfigType = TypeVar("PipelineRunContextConfigType", bound=NonMutableConfig)


class RuntimeAnalyticsInfo(GenericModel):
    """
    Salt analytics runtime information.
    """

    version: str


class RuntimeSaltInfo(GenericModel):
    """
    Salt runtime information.
    """

    id: str  # noqa: A003
    role: str
    version: str
    version_info: Tuple[int, ...]


class RuntimeInfo(GenericModel):
    """
    Salt analytics pipelines runtime information.
    """

    salt: RuntimeSaltInfo
    analytics: RuntimeAnalyticsInfo


class PipelineRunContext(GenericModel, Generic[PipelineRunContextConfigType]):
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
            self._info = RuntimeInfo.construct(
                salt=RuntimeSaltInfo.construct(
                    id=salt_id,
                    role=salt_config["__role"],
                    version=salt.version.__version__,
                    version_info=salt.version.__saltstack_version__.info,
                ),
                analytics=RuntimeAnalyticsInfo.construct(
                    version=saf.__version__,
                ),
            )
        return self._info
