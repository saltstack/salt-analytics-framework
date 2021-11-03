# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Date and time related utilities.
"""
from datetime import datetime
from datetime import timezone


def utcnow() -> datetime:
    """
    Return the current date and time with the timezone set to UTC.
    """
    return datetime.now(tz=timezone.utc)
