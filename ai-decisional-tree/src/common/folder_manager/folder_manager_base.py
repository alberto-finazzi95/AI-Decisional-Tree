"""
@brief Provide filesystem path composition and folder/file operations.
"""

from pathlib import Path
from typing import overload

import src.common.folder_manager.data_structures as ds
import src.common.folder_manager.exceptions as ex
from src.common.os_manager import OsManager, OsWrapper


class FolderManagerBase:
    """
    @brief Compose filesystem paths and perform file and directory operations.
    """

    def __init__(self, base_path: str, os_manager: OsManager | None = None):
        """
        @brief Initialize path operations with a base directory and filesystem helper.
        @param base_path: Base directory used to compose paths.
        @param os_manager: Optional filesystem-operation implementation.
        """
        self.base_path: Path = Path(base_path)
        self._os_manager: OsManager = os_manager if os_manager is not None else OsWrapper()

    def get_file_path(
        self, folder_name: str | ds.FolderName, file_name: str | ds.FileName, str_format: bool
    ) -> str | Path:
        """
        @brief Compose a path from the base directory, folder, and file names.
        @param folder_name: Directory name or path.
        @param file_name: File name to resolve.
        @param str_format: Whether to return the path as a string.
        @return: The str | Path produced by this operation.
        """
        file_path: Path = self.base_path / folder_name / file_name
        if str_format:
            return str(file_path)
        return file_path

    @overload
    def file_exists(self, folder_name: str | ds.FolderName, file_name: str | ds.FileName) -> bool:
        """
        @brief Declare the folder-and-file form of the file existence check.
        @param folder_name: Directory containing the file.
        @param file_name: Name of the file to check.
        @return: True if the path refers to an existing file.
        """
        ...

    # Also accept the complete path without separate folder and file names.
    @overload
    def file_exists(self, file_path: Path) -> bool:
        """
        @brief Declare the complete-path form of the file existence check.
        @param file_path: Complete path to the file.
        @return: True if the path refers to an existing file.
        """
        ...

    def file_exists(self, folder_or_path: any, file_name: any = None) -> bool:
        """
        @brief Check whether the specified path refers to an existing file.
        @param folder_or_path: Folder name or complete file path.
        @param file_name: File name to resolve.
        @return: The bool produced by this operation.
        """
        if file_name is None:
            file_path = folder_or_path
        else:
            file_path = self.get_file_path(folder_or_path, file_name, str_format=False)

        return self._os_manager.exists(file_path) and self._os_manager.is_file(file_path)

    def folder_exists(self, folder_name: str | ds.FolderName) -> bool:
        """
        @brief Check whether the specified path refers to an existing directory.
        @param folder_name: Directory name or path.
        @return: The bool produced by this operation.
        """
        folder_path: str | Path = self.get_folder_path(folder_name, str_format=False)
        return self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path)

    def get_file_path_if_exist(
        self, folder_name: str | ds.FolderName, file_name: str | ds.FileName, str_format: bool = True
    ) -> str | Path:
        """
        @brief Return a file path, raising an error if the file is absent.
        @param folder_name: Directory name or path.
        @param file_name: File name to resolve.
        @param str_format: Whether to return the path as a string.
        @return: The str | Path produced by this operation.
        @throws NoFileException: If the operation encounters this error.
        """
        if not self.file_exists(folder_name, file_name):
            raise ex.NoFileException(folder_name, file_name)
        return self.get_file_path(folder_name, file_name, str_format=str_format)

    def create_folder(self, folder_name: str | ds.FolderName) -> None:
        """
        @brief Create the requested directory, including missing parent directories.
        @param folder_name: Directory name or path.
        """
        folder_path: Path = self.base_path / folder_name
        self._os_manager.mkdir(folder_path, parents=True, exist_ok=True)

    def get_folder_path(self, folder_name: str | ds.FolderName, str_format: bool = True) -> str | Path:
        """
        @brief Compose a path to a directory beneath the base directory.
        @param folder_name: Directory name or path.
        @param str_format: Whether to return the path as a string.
        @return: The str | Path produced by this operation.
        """
        folder_path: Path = self.base_path / folder_name
        if str_format:
            return str(folder_path)
        return folder_path

    def compose_folders(self, *folder_names: str | ds.FolderName, str_format: bool = True) -> str | Path:
        """
        @brief Join directory components beneath the base directory.
        @param str_format: Whether to return the path as a string.
        @param folder_names: Additional positional arguments.
        @return: The str | Path produced by this operation.
        """
        composed_path: Path = self.base_path.joinpath(*folder_names)
        if str_format:
            return str(composed_path)
        return composed_path

    def delete_folder(self, folder_name: ds.FolderName) -> None:
        """
        @brief Delete a directory and its contents when it exists.
        @param folder_name: Directory name or path.
        """
        folder_path: Path = self.base_path / folder_name
        self._delete_folder(folder_path)

    def _delete_folder(self, folder_path: Path) -> None:
        """
        @brief Recursively remove a directory's contents and then the directory.
        @param folder_path: Directory path to remove if it exists.
        """
        if self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path):
            for item in self._os_manager.iterdir(folder_path):
                if self._os_manager.is_file(item):
                    self._os_manager.unlink(item)
                else:
                    self._delete_folder(item)
            self._os_manager.rmdir(folder_path)

    def get_subfolders(self, folder: str | Path) -> list[str]:
        """
        @brief Return the names of immediate child directories.
        @param folder: Folder used by this operation.
        @return: The list[str] produced by this operation.
        @throws NoFolderFound: If the operation encounters this error.
        """
        if not self._os_manager.exists(folder) or not self._os_manager.is_dir(folder):
            raise ex.NoFolderFound(folder)
        return [item.name for item in self._os_manager.iterdir(folder) if self._os_manager.is_dir(item)]
