from __future__ import annotations

import ast
import logging
import os
import shutil
import subprocess
from importlib import import_module
from itertools import chain
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any
from unittest.mock import patch
from zipfile import ZipFile

import cjdk
import scyjava
import scyjava.config
from stubgenj import generateJavaStubs

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger("scyjava_stubs")

# default java vendor and version that will be installed if needed
DEFAULT_JAVA = "zulu-jre"
DEFAULT_JAVA_VERSION = "11"

# default maven url and sha512 that will be installed if needed
DEFAULT_MAVEN = "tgz+https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz"
DEFAULT_MAVEN_SHA512 = "a555254d6b53d267965a3404ecb14e53c3827c09c3b94b5678835887ab404556bfaf78dcfe03ba76fa2508649dca8531c74bca4d5846513522404d48e8c4ac8b"  # noqa

# the "real" init file that goes into the stub package
INIT_TEMPLATE = """\
from scyjava_stubs import dynamic_import

__all__, __getattr__ = dynamic_import(__name__, __file__, {endpoints})
"""


def generate_stubs(
    endpoints: Sequence[str],
    prefixes: Sequence[str] = (),
    output_dir: str | Path = "stubs",
    maven_url: str | None = None,
    maven_sha512: str | None = None,
    convert_strings: bool = True,
    include_javadoc: bool = True,
    add_runtime_imports: bool = True,
    remove_namespace_only_stubs: bool = False,
) -> None:
    """Generate stubs for the given maven endpoints.

    Parameters
    ----------
    endpoints : Sequence[str]
        The maven endpoints to generate stubs for. This should be a list of GAV
        coordinates, e.g. ["org.apache.commons:commons-lang3:3.12.0"].
    prefixes : Sequence[str], optional
        The prefixes to generate stubs for. This should be a list of Java class
        prefixes that you expect to find in the endpoints. For example,
        ["org.apache.commons"].  If not provided, the prefixes will be
        automatically determined from the jar files provided by endpoints.
    output_dir : str | Path, optional
        The directory to write the generated stubs to. Defaults to "stubs".
    maven_url : str | None, optional
        The URL to download Maven from. If not provided, the default Maven
        URL will be used. This can be a tgz URL or a local path to a Maven
        installation. If a local path is provided, it should point to the
        Maven installation directory.
    maven_sha512 : str | None, optional
        The SHA512 checksum of the Maven archive, if providing the URL.
    convert_strings : bool, optional
        Whether to cast Java strings to Python strings in the stubs. Defaults to True.
        NOTE: This leads to type stubs that may not be strictly accurate at runtime.
        The actual runtime type of strings is determined by whether jpype.startJVM is
        called with the `convertStrings` argument set to True or False.  By setting
        this `convert_strings` argument to true, the type stubs will be generated as if
        `convertStrings` is set to True: that is, all string types will be listed as
        `str` rather than `java.lang.String | str`.  This is a safer default (as `str`)
        is a subtype of `java.lang.String`), but may lead to type errors in some cases.
    include_javadoc : bool, optional
        Whether to include Javadoc in the generated stubs. Defaults to True.
    add_runtime_imports : bool, optional
        Whether to add runtime imports to the generated stubs. Defaults to True.
        This is useful if you want to use the stubs as a runtime package with type
        safety.
    remove_namespace_only_stubs : bool, optional
        Whether to remove stubs that export no names beyond a single
        `__module_protocol__`. This leaves some folders as PEP420 implicit namespace
        folders. Defaults to False.  Setting this to `True` is useful if you want to
        merge the generated stubs with other stubs in the same namespace.  Without this,
        the `__init__.pyi` for any given module will be whatever whatever the *last*
        stub generator wrote to it (and therefore inaccurate).
    """
    import jpype.imports

    startJVM = jpype.startJVM

    scyjava.config.endpoints.extend(endpoints)
    # make sure we have a basic logger ?
    # scyjava.config.endpoints.append("org.slf4j:slf4j-simple")

    vendor = os.environ.get("JAVA_VENDOR", DEFAULT_JAVA)
    version = os.environ.get("JAVA_VERSION", DEFAULT_JAVA_VERSION)

    with cjdk.java_env(vendor=vendor, version=version):

        def _patched_start(*args: Any, **kwargs: Any) -> None:
            kwargs.setdefault("convertStrings", convert_strings)
            startJVM(*args, **kwargs)

        with patch.object(jpype, "startJVM", new=_patched_start):
            _ensure_mvn(maven_url, maven_sha512)
            scyjava.start_jvm()

        _prefixes = set(prefixes)
        if not _prefixes:
            cp = jpype.getClassPath(env=False)
            ep_artifacts = tuple(ep.split(":")[1] for ep in endpoints)
            for j in cp.split(os.pathsep):
                if Path(j).name.startswith(ep_artifacts):
                    _prefixes.update(list_top_level_packages(j))

        prefixes = sorted(_prefixes)
        logger.info(f"Using endpoints: {scyjava.config.endpoints!r}")
        logger.info(f"Generating stubs for: {prefixes}")
        logger.info(f"Writing stubs to: {output_dir}")

        jmodules = [import_module(prefix) for prefix in prefixes]
        generateJavaStubs(
            jmodules,
            useStubsSuffix=False,
            outputDir=str(output_dir),
            jpypeJPackageStubs=False,
            includeJavadoc=include_javadoc,
        )

    output_dir = Path(output_dir)
    if add_runtime_imports:
        logger.info("Adding runtime imports to generated stubs")
    for stub in output_dir.rglob("*.pyi"):
        stub_ast = ast.parse(stub.read_text())
        members = {node.name for node in stub_ast.body if hasattr(node, "name")}
        if members == {"__module_protocol__"}:
            # this is simply a module stub... no exports
            if remove_namespace_only_stubs:
                logger.info("Removing namespace only stub %s", stub)
                stub.unlink()
            continue
        if add_runtime_imports:
            real_import = stub.with_suffix(".py")
            endpoint_args = ", ".join(repr(x) for x in endpoints)
            real_import.write_text(INIT_TEMPLATE.format(endpoints=endpoint_args))

    ruff_check(output_dir.absolute())


def ruff_check(output: Path) -> None:
    py_files = [str(x) for x in chain(output.rglob("*.py"), output.rglob("*.pyi"))]
    if shutil.which("ruff"):
        logger.info(
            "Running ruff check on %d generated stubs in % s",
            len(py_files),
            str(output),
        )
        subprocess.run(
            [
                "ruff",
                "check",
                *py_files,
                "--quiet",
                "--fix-only",
                "--unsafe-fixes",
                "--select=E,W,F,I,UP,C4,B,RUF,TC,TID",
            ]
        )
        logger.info("Running ruff format")
        subprocess.run(["ruff", "format", *py_files, "--quiet"])


def list_top_level_packages(jar_path: str) -> set[str]:
    """Inspect a JAR file and return the set of top-level Java package names."""
    packages: set[str] = set()
    with ZipFile(jar_path, "r") as jar:
        # find all classes
        class_dirs = {
            entry.parent
            for x in jar.namelist()
            if (entry := PurePath(x)).suffix == ".class"
        }

        roots: set[PurePath] = set()
        for p in sorted(class_dirs, key=lambda p: len(p.parts)):
            # If none of the already accepted roots is a parent of p, keep p
            if not any(root in p.parents for root in roots):
                roots.add(p)
        packages.update({str(p).replace(os.sep, ".") for p in roots})

    return packages


def _ensure_mvn(maven_url: str | None = None, maven_sha512: str | None = None) -> None:
    if not shutil.which("mvn"):
        if maven_url is None:
            if maven_url := os.getenv("MAVEN_URL", None):
                maven_sha512 = os.getenv("MAVEN_SHA", None)
            else:
                maven_url = DEFAULT_MAVEN
                maven_sha512 = DEFAULT_MAVEN_SHA512
        pkg_dir = cjdk.cache_package("Maven", maven_url, sha512=maven_sha512)
        maven_bin = next(pkg_dir.rglob("mvn")).parent
        os.environ["PATH"] = os.pathsep.join([str(maven_bin), os.environ["PATH"]])

    if not shutil.which("mvn"):
        raise RuntimeError("Maven not found. Please install Maven or cjdk.")
