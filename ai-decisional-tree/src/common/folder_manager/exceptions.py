"""
@brief Define exceptions raised by folder and file operations.
"""
from pathlib import Path

import src.common.folder_manager.data_structures as ds


class NoFileException(FileNotFoundError):
    """
    @brief Raised when a requested file is missing.


    Exception raised when a file is not found.

    Attributes:
        file_path (str | ds.FileName): The path of the file that was not found.
        file_name: (str | ds.FileName): The name of the file that was not found.

    """

    def __init__(self, folder_name: str | ds.FolderName, file_name: str | ds.FileName):
        """
        @brief Create a missing-file error for the specified folder and file.
        @param folder_name: Directory name or path.
        @param file_name: File name to resolve.
        """
        file_path: str = f"{folder_name}/{file_name}"
        message: str = f"File not found: {file_path}"
        super().__init__(message)


class NoFolderFound(FileNotFoundError):
    """
    @brief Raised when a requested directory is missing.


    Exception raised when a folder is not found.

    Attributes:
        folder_path (str | ds.FolderName): The path of the folder that was not found.

    """

    def __init__(self, folder_name: str | Path):
        """
        @brief Create a missing-directory error for the specified path.
        @param folder_name: Directory name or path.
        """
        message: str = f"Folder not found: {folder_name}"
        super().__init__(message)
