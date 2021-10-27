# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""
Salt engine module.
"""
import logging

log = logging.getLogger(__name__)

__virtualname__ = "saf"


def __virtual__():
    # To force a module not to load return something like:
    #   return (False, "The salt-analytics-framework engine module is not implemented yet")
    return __virtualname__
