"""Type stub generator for maven artifacts."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("scyjava-stubs")
except PackageNotFoundError:
    __version__ = "uninstalled"

__all__ = ["__version__", "dynamic_import", "generate_stubs"]
from ._dynamic_import import dynamic_import
from ._genstubs import generate_stubs
