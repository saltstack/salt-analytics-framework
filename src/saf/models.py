# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""
Salt Analytics Framework Models.
"""
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Optional

from pydantic.fields import Field
from pydantic.main import BaseModel

from saf.utils import dt


class NamedConfigMixin(BaseModel):
    """
    Base class for configuration schemas.
    """

    name: str

    class Config:

        allow_mutation = False


class CollectConfigBase(NamedConfigMixin):
    """
    Base config schema for collect plugins.
    """


class ProcessConfigBase(NamedConfigMixin):
    """
    Base config schema for process plugins.
    """


class ForwardConfigBase(NamedConfigMixin):
    """
    Base config schema for forward plugins.
    """


class CollectedEvent(BaseModel):
    """
    Class representing each of the collected events.
    """

    data: Dict[str, Any]
    timestamp: Optional[datetime] = Field(default_factory=dt.utcnow)
