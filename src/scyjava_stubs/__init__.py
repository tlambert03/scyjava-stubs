"""Type stub generator for maven artifacts."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("scyjava-stubgen")
except PackageNotFoundError:
    __version__ = "uninstalled"

__all__ = ["generate_stubs", "dynamic_import", "__version__"]
from ._genstubs import generate_stubs
from ._dynamic_import import dynamic_import
