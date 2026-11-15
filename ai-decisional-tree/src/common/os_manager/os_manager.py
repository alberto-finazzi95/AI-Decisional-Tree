"""
@brief Define the operating-system operations used by the application.
"""
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path


class OsManager(ABC):
    """
    @brief Interface for filesystem and dataset-download operations.
    """
    @abstractmethod
    def download_dataset(self, dataset_name: str, output_dir: str) -> str:
        """
        @brief Download the named dataset into the requested output directory.
        @param dataset_name: Dataset identifier to download.
        @param output_dir: Directory where dataset files are placed.
        @return: The str produced by this operation.
        """
        pass

    @abstractmethod
    def dirname(self, path: str) -> str:
        """
        @brief Return the parent directory portion of a path.
        @param path: Filesystem path to inspect or process.
        @return: The str produced by this operation.
        """
        pass

    @abstractmethod
    def exists(self, path: str | Path) -> bool:
        """
        @brief Check whether a filesystem path exists.
        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        pass

    @abstractmethod
    def is_file(self, path: str | Path) -> bool:
        """
        @brief Check whether a path identifies a file.
        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        pass

    @abstractmethod
    def is_dir(self, path: str | Path) -> bool:
        """
        @brief Check whether a path identifies a directory.
        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        pass

    @abstractmethod
    def mkdir(self, path: str | Path, parents: bool = False, exist_ok: bool = False) -> None:
        """
        @brief Create a directory using the requested parent and existing-path options.
        @param path: Filesystem path to inspect or process.
        @param parents: Whether to create missing parent directories.
        @param exist_ok: Whether an existing directory is accepted.
        """
        pass

    @abstractmethod
    def iterdir(self, path: str | Path) -> Iterator[Path]:
        """
        @brief Return the immediate entries in a directory.
        @param path: Filesystem path to inspect or process.
        @return: The Iterator[Path] produced by this operation.
        """
        pass

    @abstractmethod
    def unlink(self, path: str | Path) -> None:
        """
        @brief Remove a file path.
        @param path: Filesystem path to inspect or process.
        """
        pass

    @abstractmethod
    def rmdir(self, path: str | Path) -> None:
        """
        @brief Remove an empty directory.
        @param path: Filesystem path to inspect or process.
        """
        pass
