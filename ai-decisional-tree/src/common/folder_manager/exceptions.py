import src.common.folder_manager.data_structures as ds


class NoFileException(FileNotFoundError):
    """
    Exception raised when a file is not found.

    Attributes:
        file_path (ds.FileName): The path of the file that was not found.
        file_name: (ds.FileName): The name of the file that was not found.
    """

    def __init__(self, folder_name: ds.FolderName, file_name: ds.FileName):
        file_path: str = f"{folder_name}/{file_name}"
        message: str = f"File not found: {file_path}"
        super().__init__(message)
