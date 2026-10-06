import src.common as cm
import src.config_parser as cp
import src.data.common as dcm


class DataPlotter(dcm.BaseData):
    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
            os_manager: cm.OsManager | None = None
    ):
        super().__init__(folder_manager, config_parser, os_manager)
