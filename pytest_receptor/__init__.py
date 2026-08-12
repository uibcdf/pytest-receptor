from importlib.metadata import PackageNotFoundError, version

try:
    # The version of an installed package, from its distribution metadata.
    __version__ = version("pytest-receptor")
except PackageNotFoundError:
    try:
        # A source tree that has been built at least once: versioningit wrote it.
        from ._version import __version__
    except ImportError:
        # A fresh, unbuilt checkout with no VCS metadata.
        __version__ = "0.0.0+unknown"

from .artifact import (  # noqa: E402
    Artifact,
    ArtifactError,
    ArtifactFormatError,
    ArtifactIntegrityError,
    ArtifactRecord,
    UnsupportedSchemaError,
    read_artifact,
)

__all__ = [
    "Artifact",
    "ArtifactError",
    "ArtifactFormatError",
    "ArtifactIntegrityError",
    "ArtifactRecord",
    "UnsupportedSchemaError",
    "__version__",
    "read_artifact",
]
