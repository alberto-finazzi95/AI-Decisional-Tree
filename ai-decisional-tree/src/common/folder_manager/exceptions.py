from pathlib import Path
import src.common.folder_manager.data_structures as ds


class NoFileException(FileNotFoundError):
    """
    Exception raised when a file is not found.

    Attributes:
        file_path (str | ds.FileName): The path of the file that was not found.
        file_name: (str | ds.FileName): The name of the file that was not found.
    """

    def __init__(self, folder_name: str | ds.FolderName, file_name: str | ds.FileName):
        file_path: str = f"{folder_name}/{file_name}"
        message: str = f"File not found: {file_path}"
        super().__init__(message)


class NoFolderFound(FileNotFoundError):
    """
    Exception raised when a folder is not found.

    Attributes:
        folder_path (str | ds.FolderName): The path of the folder that was not found.
    """

    def __init__(self, folder_name: str | Path):
        message: str = f"Folder not found: {folder_name}"
        super().__init__(message)
