"""
@brief Implement operating-system operations using pathlib and dataset download support.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import kagglehub
import truststore
from requests.exceptions import SSLError

import src.common.os_manager as osm


class OsWrapper(osm.OsManager):
    """
    @brief Implement filesystem and dataset-download operations using standard libraries.
    """

    def download_dataset(self, dataset_name: str, output_dir: str) -> str:
        """
        @brief Download the named dataset into the requested output directory.
        @param dataset_name: Dataset identifier to download.
        @param output_dir: Directory where dataset files are placed.
        @return: The str produced by this operation.
        """
        try:
            return kagglehub.dataset_download(dataset_name, output_dir=output_dir)
        except SSLError as error:
            if "CERTIFICATE_VERIFY_FAILED" not in str(error):
                raise
            print("Certificate verification failed; retrying with system certificates.")
            truststore.inject_into_ssl()
            return kagglehub.dataset_download(dataset_name, output_dir=output_dir)

    def dirname(self, path: str) -> str:
        """
        @brief Return the parent directory portion of a path.
        @param path: Filesystem path to inspect or process.
        @return: The str produced by this operation.
        """
        return os.path.dirname(path)

    def exists(self, path: str | Path) -> bool:
        """
        @brief Check whether a filesystem path exists.
        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        return Path(path).exists()

    def is_file(self, path: str | Path) -> bool:
        """
        @brief Check whether a path identifies a file.
        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        return Path(path).is_file()

    def is_dir(self, path: str | Path) -> bool:
        """
        @brief Check whether a path identifies a directory.
        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        return Path(path).is_dir()

    def mkdir(self, path: str | Path, parents: bool = False, exist_ok: bool = False) -> None:
        """
        @brief Create a directory using the requested parent and existing-path options.
        @param path: Filesystem path to inspect or process.
        @param parents: Whether to create missing parent directories.
        @param exist_ok: Whether an existing directory is accepted.
        """
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def iterdir(self, path: str | Path) -> Iterator[Path]:
        """
        @brief Return the immediate entries in a directory.
        @param path: Filesystem path to inspect or process.
        @return: The Iterator[Path] produced by this operation.
        """
        return Path(path).iterdir()

    def unlink(self, path: str | Path) -> None:
        """
        @brief Remove a file path.
        @param path: Filesystem path to inspect or process.
        """
        Path(path).unlink()

    def rmdir(self, path: str | Path) -> None:
        """
        @brief Remove an empty directory.
        @param path: Filesystem path to inspect or process.
        """
        Path(path).rmdir()
