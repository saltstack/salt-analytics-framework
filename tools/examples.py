# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
These commands are used for the examples.
"""
from __future__ import annotations

import logging
import pathlib
import shutil
from typing import Optional

from ptscripts import Context
from ptscripts import command_group

log = logging.getLogger(__name__)

REPO_ROOT = pathlib.Path(__file__).parent.parent

# Define the command group
cgroup = command_group(name="examples", help="Examples Related Commands", description=__doc__)


@cgroup.command(
    name="elastic",
    arguments={
        "command": {
            "help": "The docker-compose command to run",
        },
        "rebuild_pkg": {
            "help": "Force salt-analytics package rebuild.",
        },
        "rebuild_examples_pkg": {
            "help": "Force salt-analytics.examples package rebuild.",
        },
        "docker_compose_args": {
            "help": "Extra arguments to pass to docker-compose",
            "nargs": "*",
        },
    },
)
def elastic(
    ctx: Context,
    command: str,
    rebuild_pkg: bool = False,
    rebuild_examples_pkg: bool = False,
    docker_compose_args: Optional[list[str]] = None,
):
    """
    Elastic Search Example docker-compose.
    """
    if docker_compose_args is None:
        docker_compose_args = []

    if command == "build":
        nox = shutil.which("nox")
        if nox is None:
            ctx.error(
                "The 'nox' binary was not found. Please install it: python -m pip install nox"
            )
            ctx.exit(1)
        existing_whl = list(REPO_ROOT.joinpath("dist").glob("*.whl"))
        if not existing_whl or (existing_whl and rebuild_pkg):
            ret = ctx.run(nox, "--force-color", "-e", "build")
            if ret.returncode:
                ctx.error("Failed to build the salt-analytics package")
                ctx.exit(1)
        existing_whl = list(REPO_ROOT.joinpath("examples", "dist").glob("*.whl"))
        if not existing_whl or (existing_whl and rebuild_examples_pkg):
            ret = ctx.run(nox, "--force-color", "-e", "build", "--", "examples")
            if ret.returncode:
                ctx.error("Failed to build the salt-analytics.examples package")
                ctx.exit(1)

    docker_compose = shutil.which("docker-compose")
    if docker_compose is None:
        ctx.error("The 'docker-compose' binary was not found. Please install it")
        ctx.exit(1)

    ret = ctx.run(
        docker_compose,
        "-f",
        "docker/elastic/docker-compose.yml",
        command,
        *docker_compose_args,
        interactive=True,
    )
    if ret.returncode:
        ctx.error(f"Failed to run 'docker-compose {command}'")
        ctx.exit(1)
    ctx.exit(0)
