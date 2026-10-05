import src.common.folder_manager.data_structures as ds
import src.common.folder_manager.folder_manager_base as fmb
from src.common.os_manager import OsManager


class FolderManager(fmb.FolderManagerBase):
    def __init__(self, base_path: str, os_manager: OsManager | None = None):
        super().__init__(base_path, os_manager)

    @property
    def config_file_path(self) -> str:
        return self.get_file_path_if_exist(ds.FolderName.CONFIG, ds.FileName.CONFIG)
