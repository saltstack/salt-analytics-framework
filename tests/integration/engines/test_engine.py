# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import time

import pytest


@pytest.mark.usefixtures("master")
def test_events_dumped_to_disk(analytics_events_dump_directory):
    timeout = 10
    while timeout:
        time.sleep(1)
        timeout -= 1
        if len(list(analytics_events_dump_directory.iterdir())) > 3:
            break
    else:
        pytest.fail(f"Failed to find dumped events in {analytics_events_dump_directory}")
