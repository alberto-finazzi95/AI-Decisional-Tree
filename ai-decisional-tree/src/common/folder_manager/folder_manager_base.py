from abc import ABC
from pathlib import Path

import src.common.folder_manager.exceptions as ex
import src.common.folder_manager.data_structures as ds

class FolderManagerBase(ABC):
    def __init__(self, base_path: str):
        self.base_path: Path = Path(base_path)

    def _get_file_path(self, folder_name: ds.FolderName, file_name: ds.FileName, str_format: bool) -> str | Path:
        file_path: Path = self.base_path / folder_name / file_name
        if str_format:
            return str(file_path)
        return file_path

    def file_exists(self, folder_name: ds.FolderName, file_name: ds.FileName) -> bool:
        file_path: Path = self._get_file_path(folder_name, file_name, str_format=False)
        return file_path.exists() and file_path.is_file()

    def folder_exists(self, folder_name: ds.FolderName) -> bool:
        folder_path: Path = self.get_folder_path(folder_name)
        return folder_path.exists() and folder_path.is_dir()

    def get_file_path(self, folder_name: ds.FolderName, file_name: ds.FileName, str_format: bool = True) -> str | Path:
        if not self.file_exists(folder_name, file_name):
            raise ex.NoFileException(folder_name, file_name)
        return self._get_file_path(folder_name, file_name, str_format=str_format)

    def create_folder(self, folder_name: str | ds.FolderName):
        folder_path: Path = self.base_path / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

    def get_folder_path(self, folder_name: ds.FolderName) -> Path:
        return self.base_path / folder_name

    def delete_folder(self, folder_name: ds.FolderName) -> None:
        folder_path: Path = self.base_path / folder_name
        if folder_path.exists() and folder_path.is_dir():
            for item in folder_path.iterdir():
                if item.is_file():
                    item.unlink()
                else:
                    self.delete_folder(item.name)
            folder_path.rmdir()