from abc import ABC
from pathlib import Path

import src.common.folder_manager.exceptions as ex
import src.common.folder_manager.data_structures as ds
from src.common.os_manager import OsManager, OsWrapper

class FolderManagerBase(ABC):
    def __init__(self, base_path: str, os_manager: OsManager | None = None):
        self.base_path: Path = Path(base_path)
        self._os_manager: OsManager = os_manager if os_manager is not None else OsWrapper()

    def get_file_path(self, folder_name: str | ds.FolderName, file_name: str | ds.FileName, str_format: bool) -> str | Path:
        file_path: Path = self.base_path / folder_name / file_name
        if str_format:
            return str(file_path)
        return file_path

    def file_exists(self, folder_name: str | ds.FolderName, file_name: str | ds.FileName) -> bool:
        file_path: str | Path = self.get_file_path(folder_name, file_name, str_format=False)
        return self._os_manager.exists(file_path) and self._os_manager.is_file(file_path)

    def folder_exists(self, folder_name: str | ds.FolderName) -> bool:
        folder_path: str | Path = self.get_folder_path(folder_name, str_format=False)
        return self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path)

    def get_file_path_if_exist(self, folder_name: str | ds.FolderName, file_name: str | ds.FileName, str_format: bool = True) -> str | Path:
        if not self.file_exists(folder_name, file_name):
            raise ex.NoFileException(folder_name, file_name)
        return self.get_file_path(folder_name, file_name, str_format=str_format)

    def create_folder(self, folder_name: str | ds.FolderName) -> None:
        folder_path: Path = self.base_path / folder_name
        self._os_manager.mkdir(folder_path, parents=True, exist_ok=True)

    def get_folder_path(self, folder_name: str | ds.FolderName, str_format: bool = True) -> str | Path:
        folder_path: Path = self.base_path / folder_name
        if str_format:
            return str(folder_path)
        return folder_path

    def delete_folder(self, folder_name: ds.FolderName) -> None:
        folder_path: Path = self.base_path / folder_name
        self._delete_folder(folder_path)

    def _delete_folder(self, folder_path: Path) -> None:
        if self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path):
            for item in self._os_manager.iterdir(folder_path):
                if self._os_manager.is_file(item):
                    self._os_manager.unlink(item)
                else:
                    self._delete_folder(item)
            self._os_manager.rmdir(folder_path)