from abc import ABC

import src.common as cm
import src.config_parser as cp


class BaseData(ABC):
    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
            os_manager: cm.OsManager | None = None
    ):
        self._folder_manager: cm.FolderManager = folder_manager
        self._config_parser: cp.ConfigParser = config_parser
        self._os_manager: cm.OsManager = os_manager if os_manager is not None else cm.OsWrapper()

    def folder_exists(self, folder_path: str) -> bool:
        return self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path)