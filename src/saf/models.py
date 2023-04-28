# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Salt Analytics Framework Models.
"""
from __future__ import annotations

import logging
from datetime import datetime
from types import ModuleType
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import PrivateAttr
from pydantic import validator
from pydantic.generics import GenericModel

from saf.plugins import PluginsList
from saf.utils import dt


log = logging.getLogger(__name__)


class NonMutableModel(BaseModel):
    """
    Base class for non mutable models.
    """

    class Config:
        allow_mutation = False


class NonMutableConfig(BaseModel):
    """
    Base class for non-mutable configurations.
    """

    _parent: AnalyticsConfig = PrivateAttr()

    @property
    def parent(self) -> AnalyticsConfig:
        """
        Return the parent configuration schema.
        """
        return self._parent

    class Config:
        allow_mutation = False
        underscore_attrs_are_private = True


class PluginConfigMixin(NonMutableConfig):
    """
    Base class for plugin configuration schemas.
    """

    plugin: str

    _name: str = PrivateAttr()

    @property
    def name(self) -> str:
        """
        Return the plugin name as defined in the configuration file.
        """
        return self._name

    @property
    def loaded_plugin(self) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        raise NotImplementedError


class CollectConfigBase(PluginConfigMixin):
    """
    Base config schema for collect plugins.
    """

    def __new__(  # pylint: disable=unused-argument
        cls,
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
    def loaded_plugin(self) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        return PluginsList.instance().collectors[self.plugin]


class ProcessConfigBase(PluginConfigMixin):
    """
    Base config schema for process plugins.
    """

    def __new__(  # pylint: disable=unused-argument
        cls,
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
    def loaded_plugin(self) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        return PluginsList.instance().processors[self.plugin]


class ForwardConfigBase(PluginConfigMixin):
    """
    Base config schema for forward plugins.
    """

    def __new__(  # pylint: disable=unused-argument
        cls,
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
    def loaded_plugin(self) -> ModuleType:
        """
        Return the plugin instance(module) for which this configuration refers to.
        """
        return PluginsList.instance().forwarders[self.plugin]


class PipelineConfig(NonMutableConfig):
    """
    Base config schema for pipeline configuration.
    """

    collect: str
    process: List[str] = Field(default_factory=list)
    forward: List[str]
    enabled: bool = True
    concurrent_forwarders: bool = True

    _name: str = PrivateAttr()

    @property
    def name(self) -> str:
        """
        Return the pipeline name as defined in the configuration file.
        """
        return self._name


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
    def _validate_pipelines(cls, pipelines: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        for name, data in pipelines.items():
            collect = data["collect"]
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

    def _init_private_attributes(self) -> None:
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

    data: Dict[str, Any]
    timestamp: Optional[datetime] = Field(default_factory=dt.utcnow)


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
            _stamp = datetime.fromisoformat(stamp)
        except AttributeError:  # pragma: no cover
            # Python < 3.7
            _stamp = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%S.%f")
        return _stamp

    @validator("stamp")
    @classmethod
    def _validate_stamp(cls, value: Union[str, datetime]) -> datetime:
        if isinstance(value, datetime):
            return value
        return SaltEvent._convert_stamp(value)


PipelineRunContextConfigType = TypeVar("PipelineRunContextConfigType", bound=NonMutableConfig)


class PipelineRunContext(GenericModel, Generic[PipelineRunContextConfigType]):
    """
    Class representing a pipeline run context.
    """

    config: PipelineRunContextConfigType
    cache: Dict[str, Any] = Field(default_factory=dict)
    shared_cache: Dict[str, Any] = Field(default_factory=dict)

    @property
    def pipeline_config(self) -> AnalyticsConfig:
        """
        Return the analytics configuration.
        """
        return self.config.parent

    @property
    def salt_config(self) -> Dict[str, Any]:
        """
        Return the salt configuration.
        """
        config: Dict[str, Any] = self.config.parent.salt_config
        return config
