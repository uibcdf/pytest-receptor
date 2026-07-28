from importlib.metadata import version, PackageNotFoundError

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
