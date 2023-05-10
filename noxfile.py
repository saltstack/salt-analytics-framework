# Copyright 2021-2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import contextlib
import datetime
import gzip
import json
import os
import pathlib
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

import nox
from nox.command import CommandFailed

# Nox options
#  Reuse existing virtualenvs
nox.options.reuse_existing_virtualenvs = True
#  Don't fail on missing interpreters
nox.options.error_on_missing_interpreters = False

# Python versions to test against
PYTHON_VERSIONS = ("3", "3.7", "3.8", "3.9", "3.10")
# Be verbose when running under a CI context
CI_RUN = os.environ.get("CI") is not None
PIP_INSTALL_SILENT = CI_RUN is False
SKIP_REQUIREMENTS_INSTALL = "SKIP_REQUIREMENTS_INSTALL" in os.environ
EXTRA_REQUIREMENTS_INSTALL = os.environ.get("EXTRA_REQUIREMENTS_INSTALL")

COVERAGE_VERSION_REQUIREMENT = "coverage==6.2"
SALT_REQUIREMENT = os.environ.get("SALT_REQUIREMENT") or "salt>=3005"
if SALT_REQUIREMENT == "salt==master":
    SALT_REQUIREMENT = "git+https://github.com/saltstack/salt.git@master"

REPO_ROOT = pathlib.Path(os.path.dirname(__file__)).resolve()
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
IS_WINDOWS = sys.platform.lower().startswith("win")
ONEDIR_ARTIFACT_PATH = ARTIFACTS_DIR / "salt"
if IS_WINDOWS:
    ONEDIR_PYTHON_PATH = ONEDIR_ARTIFACT_PATH / "Scripts" / "python.exe"
else:
    ONEDIR_PYTHON_PATH = ONEDIR_ARTIFACT_PATH / "bin" / "python3"

# Prevent Python from writing bytecode
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Global Path Definitions
REPO_ROOT = pathlib.Path(__file__).resolve().parent
# Change current directory to REPO_ROOT
os.chdir(str(REPO_ROOT))

ARTIFACTS_DIR = REPO_ROOT / "artifacts"
# Make sure the artifacts directory exists
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
RUNTESTS_LOGFILE = ARTIFACTS_DIR / "runtests-{}.log".format(
    datetime.datetime.now().strftime("%Y%m%d%H%M%S.%f")
)
COVERAGE_REPORT_DB = REPO_ROOT / ".coverage"
COVERAGE_REPORT_PROJECT = ARTIFACTS_DIR.relative_to(REPO_ROOT) / "coverage-project.xml"
COVERAGE_REPORT_TESTS = ARTIFACTS_DIR.relative_to(REPO_ROOT) / "coverage-tests.xml"
JUNIT_REPORT = ARTIFACTS_DIR.relative_to(REPO_ROOT) / "junit-report.xml"


def _get_session_python_version_info(session):
    try:
        version_info = session._runner._real_python_version_info
    except AttributeError:
        session_py_version = session.run_always(
            "python",
            "-c",
            'import sys; sys.stdout.write("{}.{}.{}".format(*sys.version_info))',
            silent=True,
            log=False,
        )
        version_info = tuple(int(part) for part in session_py_version.split(".") if part.isdigit())
        session._runner._real_python_version_info = version_info
    return version_info


def _get_pydir(session):
    version_info = _get_session_python_version_info(session)
    if version_info < (3, 7):
        session.error("Only Python >= 3.7 is supported")
    return "py{}.{}".format(*version_info)


def _install_requirements(
    session,
    *passed_requirements,
    install_coverage_requirements=True,
    install_test_requirements=True,
    install_source=False,
    install_salt=True,
    install_extras=None,
    onedir=False,
):
    install_extras = install_extras or []
    if SKIP_REQUIREMENTS_INSTALL is False:
        # Always have the wheel package installed
        session.install("--progress-bar=off", "setuptools>=65.6.3,<66", silent=PIP_INSTALL_SILENT)
        session.install("--progress-bar=off", "wheel", silent=PIP_INSTALL_SILENT)
        if install_coverage_requirements:
            session.install(
                "--progress-bar=off", COVERAGE_VERSION_REQUIREMENT, silent=PIP_INSTALL_SILENT
            )

        if EXTRA_REQUIREMENTS_INSTALL:
            session.log(
                "Installing the following extra requirements because the "
                "EXTRA_REQUIREMENTS_INSTALL environment variable was set: "
                "EXTRA_REQUIREMENTS_INSTALL='%s'",
                EXTRA_REQUIREMENTS_INSTALL,
            )
            install_command = ["--progress-bar=off"]
            install_command += [req.strip() for req in EXTRA_REQUIREMENTS_INSTALL.split()]
            session.install(*install_command, silent=PIP_INSTALL_SILENT)

        if onedir is False and install_salt:
            session.install("--progress-bar=off", SALT_REQUIREMENT, silent=PIP_INSTALL_SILENT)

        if install_test_requirements:
            install_extras.append("tests")

        if passed_requirements:
            session.install("--progress-bar=off", *passed_requirements, silent=PIP_INSTALL_SILENT)

        if install_source:
            pkg = "."
            if install_extras:
                pkg += f"[{','.join(install_extras)}]"
            args = ["--progress-bar=off"]
            if onedir is False:
                args.append("-e")
            args.append(pkg)
            session.install(*args, silent=PIP_INSTALL_SILENT)
        elif install_extras:
            pkg = f".[{','.join(install_extras)}]"
            session.install("--progress-bar=off", pkg, silent=PIP_INSTALL_SILENT)


def _tests(session, onedir=False):
    _install_requirements(session, "jinja2<3.1", install_source=True, onedir=onedir)

    sitecustomize_dir = session.run("salt-factories", "--coverage", silent=True, log=False)
    python_path_env_var = os.environ.get("PYTHONPATH") or None
    if python_path_env_var is None:
        python_path_env_var = sitecustomize_dir
    else:
        python_path_entries = python_path_env_var.split(os.pathsep)
        if sitecustomize_dir in python_path_entries:
            python_path_entries.remove(sitecustomize_dir)
        python_path_entries.insert(0, sitecustomize_dir)
        python_path_env_var = os.pathsep.join(python_path_entries)

    env = {
        # The updated python path so that sitecustomize is importable
        "PYTHONPATH": python_path_env_var,
        # The full path to the .coverage data file. Makes sure we always write
        # them to the same directory
        "COVERAGE_FILE": str(COVERAGE_REPORT_DB),
        # Instruct sub processes to also run under coverage
        "COVERAGE_PROCESS_START": str(REPO_ROOT / ".coveragerc"),
        "ONEDIR_TESTRUN": "1" if onedir else "0",
    }

    session.run("coverage", "erase")
    args = [
        "--rootdir",
        str(REPO_ROOT),
        f"--log-file={RUNTESTS_LOGFILE.relative_to(REPO_ROOT)}",
        "--log-file-level=debug",
        "--show-capture=no",
        f"--junitxml={JUNIT_REPORT}",
        "--showlocals",
        "--strict-markers",
        "-ra",
        "-s",
    ]
    if session._runner.global_config.forcecolor:
        args.append("--color=yes")
    if not session.posargs:
        args.append("tests/")
    else:
        for arg in session.posargs:
            if arg.startswith("--color") and args[0].startswith("--color"):
                args.pop(0)
            args.append(arg)
        for arg in session.posargs:
            if arg.startswith("-"):
                continue
            if arg.startswith(f"tests{os.sep}"):
                break
            try:
                pathlib.Path(arg).resolve().relative_to(REPO_ROOT / "tests")
                break
            except ValueError:
                continue
        else:
            args.append("tests/")
    try:
        session.run("coverage", "run", "-m", "pytest", *args, env=env)
    finally:
        # Always combine and generate the XML coverage report
        with contextlib.suppress(CommandFailed):
            session.run("coverage", "combine")

        try:
            # Generate report for salt code coverage
            session.run(
                "coverage",
                "xml",
                "-o",
                str(COVERAGE_REPORT_PROJECT),
                "--omit=tests/*",
                "--include=src/saf/*",
            )
            # Generate report for tests code coverage
            session.run(
                "coverage",
                "xml",
                "-o",
                str(COVERAGE_REPORT_TESTS),
                "--omit=src/saf/*",
                "--include=tests/*",
            )
            try:
                session.run("coverage", "report", "--show-missing", "--include=src/saf/*")
                # If you also want to display the code coverage report on the CLI
                # for the tests, comment the call above and uncomment the line below
                # session.run(
                #    "coverage", "report", "--show-missing",
                #    "--include=src/saf/*,tests/*"
                # )
            finally:
                # Move the coverage DB to artifacts/coverage in order for it to be archived by CI
                if COVERAGE_REPORT_DB.exists():
                    shutil.move(
                        str(COVERAGE_REPORT_DB), str(ARTIFACTS_DIR / COVERAGE_REPORT_DB.name)
                    )
        except CommandFailed as exc:
            # Tracking code coverage is still not working that well
            if onedir is False:
                raise exc from None


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    _tests(session, onedir=False)


@nox.session(
    python=str(ONEDIR_PYTHON_PATH),
    name="tests-onedir",
    venv_params=["--system-site-packages"],
)
def test_onedir(session):
    if not ONEDIR_ARTIFACT_PATH.exists():
        session.error(
            "The salt onedir artifact, expected to be in '{}', was not found".format(
                ONEDIR_ARTIFACT_PATH.relative_to(REPO_ROOT)
            )
        )

    _tests(session, onedir=True)


class Tee:
    """
    Python class to mimic linux tee behavior.
    """

    def __init__(self, first, second) -> None:
        self._first = first
        self._second = second

    def write(self, buf):
        wrote = self._first.write(buf)
        self._first.flush()
        self._second.write(buf)
        self._second.flush()
        return wrote

    def fileno(self):
        return self._first.fileno()


@nox.session(python="3")
def docs(session):
    """
    Build Docs.
    """
    _install_requirements(
        session,
        install_coverage_requirements=False,
        install_test_requirements=False,
        install_source=True,
        install_extras=["docs"],
    )
    os.chdir("docs/")
    session.run("make", "clean", external=True)
    # session.run("make", "linkcheck", "SPHINXOPTS=-W", external=True)
    session.run("make", "coverage", "SPHINXOPTS=-W", external=True)
    docs_coverage_file = os.path.join("_build", "html", "python.txt")
    if os.path.exists(docs_coverage_file):
        with open(docs_coverage_file, encoding="utf-8") as rfh:
            contents = rfh.readlines()[2:]
            if contents:
                session.error("\n" + "".join(contents))
    session.run("make", "html", "SPHINXOPTS=-W", external=True)
    os.chdir(str(REPO_ROOT))


@nox.session(name="docs-html", python="3")
@nox.parametrize("clean", [False, True])
@nox.parametrize("include_api_docs", [False, True])
def docs_html(session, clean, include_api_docs):
    """
    Build Sphinx HTML Documentation.

    TODO: Add option for `make linkcheck` and `make coverage`
          calls via Sphinx. Ran into problems with two when
          using Furo theme and latest Sphinx.
    """
    _install_requirements(
        session,
        install_coverage_requirements=False,
        install_test_requirements=False,
        install_source=True,
        install_extras=["docs"],
    )
    if include_api_docs:
        gen_api_docs(session)
    build_dir = Path("docs", "_build", "html")
    sphinxopts = "-Wn"
    if clean:
        sphinxopts += "E"
    args = [sphinxopts, "--keep-going", "docs", str(build_dir)]
    session.run("sphinx-build", *args, external=True)


@nox.session(name="docs-dev", python="3")
@nox.parametrize("clean", [False, True])
def docs_dev(session, clean) -> None:
    """
    Build and serve the Sphinx HTML documentation, with live reloading on file changes, via sphinx-autobuild.

    Note: Only use this in INTERACTIVE DEVELOPMENT MODE. This SHOULD NOT be called
        in CI/CD pipelines, as it will hang.
    """
    _install_requirements(
        session,
        install_coverage_requirements=False,
        install_test_requirements=False,
        install_source=True,
        install_extras=["docs", "docsauto"],
    )

    # Launching LIVE reloading Sphinx session
    build_dir = Path("docs", "_build", "html")
    args = ["--watch", ".", "--open-browser", "docs", str(build_dir)]
    if clean and build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)


@nox.session(name="docs-crosslink-info", python="3")
def docs_crosslink_info(session):
    """
    Report intersphinx cross links information.
    """
    _install_requirements(
        session,
        install_coverage_requirements=False,
        install_test_requirements=False,
        install_source=True,
        install_extras=["docs"],
    )
    os.chdir("docs/")
    intersphinx_mapping = json.loads(
        session.run(
            "python",
            "-c",
            "import json; import conf; print(json.dumps(conf.intersphinx_mapping))",
            silent=True,
            log=False,
        )
    )
    try:
        mapping_entry = intersphinx_mapping[session.posargs[0]]
    except IndexError:
        session.error(
            "You need to pass at least one argument whose value must be one of: {}".format(
                ", ".join(list(intersphinx_mapping))
            )
        )
    except KeyError:
        session.error(
            "Only acceptable values for first argument are: {}".format(
                ", ".join(list(intersphinx_mapping))
            )
        )
    session.run(
        "python", "-m", "sphinx.ext.intersphinx", mapping_entry[0].rstrip("/") + "/objects.inv"
    )
    os.chdir(str(REPO_ROOT))


@nox.session(name="gen-api-docs", python="3")
def gen_api_docs(session):
    """
    Generate API Docs.
    """
    _install_requirements(
        session,
        install_coverage_requirements=False,
        install_test_requirements=False,
        install_source=True,
        install_extras=["docs"],
    )
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree("docs/ref")

    session.run(
        "sphinx-apidoc",
        "--module-first",
        "-o",
        "docs/ref/",
        "src/",
        "src/saf/config/schemas",
    )


@nox.session(name="changelog", python="3")
@nox.parametrize("draft", [False, True])
def changelog(session, draft):
    """
    Generate changelog.
    """
    _install_requirements(
        session,
        install_coverage_requirements=False,
        install_test_requirements=False,
        install_source=False,
        install_salt=False,
        install_extras=["changelog"],
    )

    version = (
        session.run(
            "python",
            "setup.py",
            "--version",
            silent=True,
            log=False,
            stderr=None,
        )
        .strip()
        .split()[-1]
    )

    town_cmd = ["towncrier", "build", f"--version={version}"]
    if draft:
        town_cmd.append("--draft")
    session.run(*town_cmd)


@nox.session(name="release")
def release(session):
    if not session.posargs:
        session.error(
            "Forgot to pass the version to release? For example `nox -e release -- 1.1.0`"
        )
    if len(session.posargs) > 1:
        session.error(
            "Only one argument is supported by the `release` nox session. "
            "For example `nox -e release -- 1.1.0`"
        )
    version = session.posargs[0]
    try:
        session.log(f"Generating temporary {version} tag")
        session.run("git", "tag", "-as", version, "-m", f"Release {version}", external=True)
        changelog(session, draft=False)
    except CommandFailed:
        session.error("Failed to generate the temporary tag")
    # session.notify("changelog(draft=False)")
    try:
        session.log("Generating the release changelog")
        session.run(
            "git",
            "commit",
            "-a",
            "-m",
            f"Generate Changelog for version {version}",
            external=True,
        )
    except CommandFailed:
        session.error("Failed to generate the release changelog")
    try:
        session.log(f"Overwriting temporary {version} tag")
        session.run("git", "tag", "-fas", version, "-m", f"Release {version}", external=True)
    except CommandFailed:
        session.error("Failed to overwrite the temporary tag")
    session.warn("Don't forget to push the newly created tag")


class Recompress:
    """
    Helper class to re-compress a ``.tag.gz`` file to make it reproducible.
    """

    def __init__(self, mtime) -> None:
        self.mtime = int(mtime)

    def tar_reset(self, tarinfo):
        """
        Reset user, group, mtime, and mode to create reproducible tar.
        """
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"
        tarinfo.mtime = self.mtime
        if tarinfo.type == tarfile.DIRTYPE:
            tarinfo.mode = 0o755
        else:
            tarinfo.mode = 0o644
        if tarinfo.pax_headers:
            raise ValueError(tarinfo.name, tarinfo.pax_headers)
        return tarinfo

    def recompress(self, targz):
        """
        Re-compress the passed path.
        """
        tempd = pathlib.Path(tempfile.mkdtemp()).resolve()
        d_src = tempd.joinpath("src")
        d_src.mkdir()
        d_tar = tempd.joinpath(targz.stem)
        d_targz = tempd.joinpath(targz.name)
        with tarfile.open(d_tar, "w|") as wfile, tarfile.open(targz, "r:gz") as rfile:
            rfile.extractall(d_src)  # nosec
            extracted_dir = next(pathlib.Path(d_src).iterdir())
            for name in sorted(extracted_dir.rglob("*")):
                wfile.add(
                    str(name),
                    filter=self.tar_reset,
                    recursive=False,
                    arcname=str(name.relative_to(d_src)),
                )

        with open(d_tar, "rb") as rfh, gzip.GzipFile(
            fileobj=open(d_targz, "wb"), mode="wb", filename="", mtime=self.mtime
        ) as gzfile:
            while True:
                chunk = rfh.read(1024)
                if not chunk:
                    break
                gzfile.write(chunk)
        targz.unlink()
        shutil.move(str(d_targz), str(targz))


@nox.session(python="3")
def build(session):
    """
    Build source and binary distributions based off the current commit author date UNIX timestamp.

    The reason being, reproducible packages.

    .. code-block: shell

        git show -s --format=%at HEAD
    """
    shutil.rmtree("dist/", ignore_errors=True)
    if SKIP_REQUIREMENTS_INSTALL is False:
        requirements_file = REPO_ROOT / "requirements" / "build.txt"
        session.install(
            "--progress-bar=off",
            "-r",
            str(requirements_file.relative_to(REPO_ROOT)),
            silent=PIP_INSTALL_SILENT,
        )
    timestamp = session.run(
        "git",
        "show",
        "-s",
        "--format=%at",
        "HEAD",
        silent=True,
        log=False,
        stderr=None,
    ).strip()
    env = {"SOURCE_DATE_EPOCH": str(timestamp)}
    session.run(
        "python",
        "-m",
        "build",
        "--sdist",
        "--wheel",
        str(REPO_ROOT),
        env=env,
    )
    # Recreate sdist to be reproducible
    recompress = Recompress(timestamp)
    for targz in REPO_ROOT.joinpath("dist").glob("*.tar.gz"):
        session.log("Re-compressing %s...", targz.relative_to(REPO_ROOT))
        recompress.recompress(targz)

    sha256sum = shutil.which("sha256sum")
    if sha256sum:
        packages = [str(pkg.relative_to(REPO_ROOT)) for pkg in REPO_ROOT.joinpath("dist").iterdir()]
        session.run("sha256sum", *packages, external=True)
    session.run("python", "-m", "twine", "check", "dist/*")
