import src.common as cm
import src.config_parser as cp
import src.data.common as dcm



class DataAnalyzer(dcm.BaseData):
    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
            os_manager: cm.OsManager | None = None,
    ):
        super().__init__(
            folder_manager=folder_manager,
            config_parser=config_parser,
            os_manager=os_manager
        )
