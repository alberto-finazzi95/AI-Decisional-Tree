import src.common.folder_manager.data_structures as ds
import src.common.folder_manager.folder_manager_base as fmb


class FolderManager(fmb.FolderManagerBase):
    def __init__(self, base_path: str):
        super().__init__(base_path)

    @property
    def config_file_path(self) -> str:
        return self.get_file_path(ds.FolderName.CONFIG, ds.FileName.CONFIG)
