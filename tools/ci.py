# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
These commands are used in the CI pipeline.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import pathlib
import tempfile

from ptscripts import CWD
from ptscripts import Context
from ptscripts import command_group

log = logging.getLogger(__name__)

# Define the command group
cgroup = command_group(name="ci", help="CI Related Commands", description=__doc__)


@cgroup.command(
    name="download-onedir",
    arguments={
        "salt_version": {
            "help": "The salt version to download",
        },
        "platform": {
            "help": "The onedir platform to download.",
            "choices": ("linux", "windows", "macos"),
            "type": str.lower,
        },
        "arch": {
            "help": "The onedir Arch to download.",
            "type": str.lower,
        },
    },
)
def download_onedir(
    ctx: Context,
    salt_version: str,
    platform: str = "linux",
    arch: str = "x86_64",
):
    """
    Download a Salt Onedir.
    """
    if platform == "windows":
        if arch in ("x64", "x86_64"):
            ctx.info(f"Turning passed arch {arch!r} into 'amd64'")
            arch = "amd64"
        if arch not in ("amd64", "x86"):
            ctx.error("The allowed values for '--arch' on Windows are 'amd64' and 'x86'")
            ctx.exit(1)
    else:
        if arch == "arm64":
            ctx.info(f"Turning passed arch {arch!r} into 'aarch64'")
            arch = "aarch64"
        elif arch == "x64":
            ctx.info(f"Turning passed arch {arch!r} into 'x86_64'")
            arch = "x86_64"
        if arch not in ("x86_64", "aarch64"):
            ctx.error(
                f"The allowed values for '--arch' on {platform.title()} are 'x86_64', 'aarch64' or 'arm64'"
            )
            ctx.exit(1)

    artifacts_path = CWD / "artifacts"
    artifacts_path.mkdir(exist_ok=True)
    if artifacts_path.joinpath("salt").exists():
        ctx.error("The 'artifacts/salt' directory already exists ...")
        ctx.exit(1)
    repo_base_url = "https://repo.saltproject.io/salt/py3/onedir"
    if "." in salt_version and not salt_version.endswith(".x"):
        repo_base_url += "/minor"
        ctx.info(f"Targgeting Salt version {salt_version}")
    else:
        salt_version = salt_version.replace(".x", "")
        ctx.info(f"Targetting the latest Salt minor version of {salt_version}")

    repo_json_url = f"{repo_base_url}/repo.json"
    tempdir_path = pathlib.Path(tempfile.gettempdir())
    with ctx.web:
        repo_json_file = _download_file(ctx, repo_json_url, tempdir_path / "repo.json")
        repo_json_data = json.loads(repo_json_file.read_text())
        ctx.info("Contents of the downloaded 'repo.json' file:")
        ctx.print(repo_json_data, soft_wrap=True)
        if salt_version not in repo_json_data:
            ctx.error(f"Could not find the '{salt_version}' key in the downloaded 'repo.json' file")
            ctx.exit(1)
        version_details = repo_json_data[salt_version]
        selected_fname_details: dict[str, str] | None = None
        for _fname, details in version_details.items():
            if details["os"] != platform:
                continue
            if details["arch"] != arch:
                continue
            selected_fname_details = details
            break
        else:
            ctx.error(f"Could not find a onedir matching platform {platform!r} and arch {arch!r}")
            ctx.exit(1)
        ctx.info("Selected onedir archive details:")
        ctx.print(selected_fname_details, soft_wrap=True)
        onedir_url = f"{repo_base_url}/{salt_version}/{selected_fname_details['name']}"
        onedir_fpath = _download_file(
            ctx, onedir_url, tempdir_path / selected_fname_details["name"]
        )
        onedir_checksum = _get_file_checksum(onedir_fpath, "sha512")
        if onedir_checksum != selected_fname_details["SHA512"]:
            ctx.error("The 'sha512' checksum does not match")
            ctx.error(f"{onedir_checksum!r} != {selected_fname_details['SHA512']!r}")
            ctx.exit(1)

        ctx.info("The downloaded file checksum matches")
        with ctx.chdir(artifacts_path):
            ctx.info(f"Extracting {selected_fname_details['name']} to 'artifacts/' ...")
            ctx.run("tar", "xf", onedir_fpath)

        with contextlib.suppress(PermissionError):
            onedir_fpath.unlink()


def _download_file(ctx: Context, url: str, dest: str, auth: str | None = None) -> str:
    # NOTE the stream=True parameter below
    ctx.info(f"Downloading {url} ...")
    with ctx.web.get(url, stream=True, auth=auth) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return dest


def _get_file_checksum(fpath: pathlib.Path, hash_name: str) -> str:
    with fpath.open("rb") as rfh:
        try:
            digest = hashlib.file_digest(rfh, hash_name)  # type: ignore[attr-defined]
        except AttributeError:
            # Python < 3.11
            buf = bytearray(2**18)  # Reusable buffer to reduce allocations.
            view = memoryview(buf)
            digest = getattr(hashlib, hash_name)()
            while True:
                size = rfh.readinto(buf)
                if size == 0:
                    break  # EOF
                digest.update(view[:size])
    hexdigest: str = digest.hexdigest()
    return hexdigest
