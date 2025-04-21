"""Hatchling build hook for generating Java stubs."""

import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import (
    BuildHookInterface,  # pyright: ignore
)

from ._genstubs import generate_stubs


class CustomBuildHook(BuildHookInterface):
    """Custom build hook for generating Java stubs."""

    PLUGIN_NAME = "scyjava-stubs"

    def initialize(self, version: str, build_data: dict) -> None:
        """Initialize the build hook with the version and build data."""
        dest = Path(self.root, "src")
        shutil.rmtree(dest, ignore_errors=True)  # remove the old stubs

        # actually build the stubs
        coord = f"{self.config['maven_coord']}:{self.metadata.version}"
        prefixes = self.config.get("prefixes", [])
        generate_stubs(endpoints=[coord], prefixes=prefixes, output_dir=dest)

        # add all packages to the build config
        packages = [str(x.relative_to(self.root)) for x in dest.iterdir()]
        self.build_config.target_config.setdefault("packages", packages)
