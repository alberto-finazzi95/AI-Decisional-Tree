from pathlib import Path

import src.common.os_manager as osm
import src.common.folder_manager.data_structures as ds
import src.common.folder_manager.folder_manager_base as fmb


class FolderManager(fmb.FolderManagerBase):
    def __init__(self, base_path: str, os_manager: osm.OsManager | None = None):
        super().__init__(base_path, os_manager)

    @property
    def config_file_path(self) -> str | Path:
        return self.get_file_path_if_exist(ds.FolderName.CONFIG, ds.FileName.CONFIG)
