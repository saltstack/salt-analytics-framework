# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=invalid-name,missing-module-docstring,missing-function-docstring
import argparse
import pathlib
import sys
import traceback


CODE_ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = CODE_ROOT / "src" / "salt-analytics-framework"
DOC_DIR = CODE_ROOT / "docs"

DOCS_BY_KIND = {}


def make_import_path(fs_path):
    return ".".join(fs_path.with_suffix("").parts[-4:])


def make_autodocs(_):
    for path in SRC_DIR.glob("*/*.py"):
        if path.name != "__init__.py":
            kind = path.parent.name
            DOCS_BY_KIND.setdefault(kind, set()).add(path)

    for kind, paths in DOCS_BY_KIND.items():
        kind_path = DOC_DIR / "ref" / kind
        all_rst = kind_path / "all.rst"
        import_paths = []
        for path in sorted(paths):
            import_path = make_import_path(path)
            import_paths.append(import_path)
            rst_path = kind_path.joinpath(import_path).with_suffix(".rst")
            print(rst_path)
            rst_path.parent.mkdir(parents=True, exist_ok=True)
            rst_path.write_text(
                f"""
    {import_path}
    {'='*len(import_path)}

    .. automodule:: {import_path}
        :members:
    """
            )

        header_text = "execution" if kind.lower() == "modules" else kind.rstrip("s") + " modules"
        header = f"{'_'*len(header_text)}\n{header_text.title()}\n{'_'*len(header_text)}"

        all_rst.write_text(
            f"""
    .. all-salt-analytics-framework.{kind}:

    {header}

    .. autosummary::
        :toctree:

    {chr(10).join(sorted('    '+p for p in import_paths))}
    """
        )


def main(argv):
    parser = argparse.ArgumentParser(prog=__name__)
    parser.add_argument("files", nargs="+")
    options = parser.parse_args(argv)
    try:
        make_autodocs(options)
        return 0
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    print(sys.argv)
    sys.exit(main(sys.argv))
