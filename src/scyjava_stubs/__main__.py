"""The scyjava-stubs executable."""

import argparse
from ast import parse
import logging
from pathlib import Path

from ._genstubs import generate_stubs


def main() -> None:
    """The main entry point for the scyjava-stubs executable."""
    logging.basicConfig(level="INFO")
    parser = argparse.ArgumentParser(
        description="Generate Python Type Stubs for Java classes."
    )
    parser.add_argument(
        "endpoints",
        type=str,
        nargs="+",
        help="Maven endpoints to install and use (e.g. org.myproject:myproject:1.0.0)",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        help="package prefixes to generate stubs for (e.g. org.myproject), "
        "may be used multiple times",
        action="append",
        default=[],
        metavar="PREFIX",
        dest="prefix",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="path to write stubs to.",
    )
    parser.add_argument(
        "--convert-strings",
        dest="convert_strings",
        action="store_true",
        default=False,
        help="convert java.lang.String to python str in return types. "
        "consult the JPype documentation on the convertStrings flag for details",
    )
    parser.add_argument(
        "--no-javadoc",
        dest="with_javadoc",
        action="store_false",
        default=True,
        help="do not generate docstrings from JavaDoc where available",
    )

    rt_group = parser.add_mutually_exclusive_group()
    rt_group.add_argument(
        "--runtime-imports",
        dest="runtime_imports",
        action="store_true",
        default=True,
        help="Add runtime imports to the generated stubs. ",
    )
    rt_group.add_argument(
        "--no-runtime-imports", dest="runtime_imports", action="store_false"
    )

    parser.add_argument(
        "--remove-namespace-only-stubs",
        dest="remove_namespace_only_stubs",
        action="store_true",
        default=False,
        help="Remove stubs that export no names beyond a single __module_protocol__. "
        "This leaves some folders as PEP420 implicit namespace folders.",
    )

    args = parser.parse_args()

    if args.output_dir is None:
        try:
            import scyjava_stubs

            output_dir = Path(scyjava_stubs.__file__).parent / "modules"
        except ImportError:
            output_dir = Path("stubs")

    generate_stubs(
        endpoints=args.endpoints,
        prefixes=args.prefix,
        output_dir=output_dir,
        convert_strings=args.convert_strings,
        include_javadoc=args.with_javadoc,
        add_runtime_imports=args.runtime_imports,
        remove_namespace_only_stubs=args.remove_namespace_only_stubs,
    )
