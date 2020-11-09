import pickle
from abc import ABC, abstractmethod
from shutil import rmtree
from typing import Any, Union, NoReturn, Optional
from pathlib import Path


class Cache(ABC):
    """Abstract class which defines the caching interface."""

    @abstractmethod
    def __getitem__(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: Any) -> NoReturn:
        pass

    @abstractmethod
    def clear(self):  # noqa: D102
        pass

    @property
    @abstractmethod
    def path(self) -> Optional[Union[str, Path]]:  # noqa: D102
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __repr__(self) -> str:
        return str(self)


class FileCache(Cache):
    """
    Cache which persists the data into :mod:`pickle` files.

    Parameters
    ----------
    path
        Path to a directory where the files will be stored.
    """

    _suffix = ".pickle"

    def __init__(self, path: Union[str, Path]):
        if not isinstance(path, (str, Path)):
            raise TypeError(
                f"Expected `path` to be either `str` or `pathlib.Path`, "
                f"found `{type(path).__name__}`."
            )
        if not str(path):
            raise ValueError("Empty cache path.")

        self._cache_dir = Path(path)

    def __contains__(self, key: str) -> bool:
        if not key.endswith(self._suffix):
            key += self._suffix

        return (self._cache_dir / key).is_file()

    def __setitem__(self, key: str, value: Any):
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        fname = str(key)
        if not fname.endswith(self._suffix):
            fname += self._suffix

        with open(self._cache_dir / fname, "wb") as fout:
            pickle.dump(value, fout)

    def __getitem__(self, key: str) -> Any:
        if not key.endswith(self._suffix):
            key += self._suffix

        if not (self._cache_dir / key).is_file():
            raise KeyError(self._cache_dir / key)

        with open(self._cache_dir / key, "rb") as fin:
            return pickle.load(fin)

    @property
    def path(self) -> Path:
        """Return the directory where the cache files are stored."""
        return self._cache_dir

    def clear(self) -> NoReturn:
        """Remove all files and the directory under :paramref:`path`."""
        if self._cache_dir.is_dir():
            rmtree(self._cache_dir)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}[path={str(self.path)!r}]>"


class MemoryCache(dict, Cache):
    """Cache which persists the data into the memory."""

    @property
    def path(self) -> None:
        """Return nothing."""
        return None

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}[size={len(self)}]>"

    def __repr__(self) -> str:
        return str(self)


def clear_cache() -> NoReturn:
    """Remove all files from the cache :attr:`omnipath.options.cache`."""
    from omnipath import options

    options.cache.clear()


__all__ = [clear_cache]