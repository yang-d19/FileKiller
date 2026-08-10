"""FileKiller application package.

The package intentionally keeps imports lightweight. Qt and multimedia modules
are imported only by their owning modules so configuration tools can be used in
headless environments.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
