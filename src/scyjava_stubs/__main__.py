"""The scyjava-stubs executable."""

import argparse
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

    args = parser.parse_args()

    if args.output_dir is None:
        try:
            import scyjava_stubs

            output_dir = Path(scyjava_stubs.__file__).parent / "modules"
        except ImportError:
            output_dir = "stubs"

    generate_stubs(
        endpoints=args.endpoints,
        prefixes=args.prefix,
        output_dir=output_dir,
        convert_strings=args.convert_strings,
        include_javadoc=args.with_javadoc,
    )
