import numpy as np

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm



class DataAnalyzer(dcm.BaseData):
    # BRAIN WINDOWING (Isolation interval 0-80 HU)
    BR_W_L: int = 40
    BR_W_W: int = 80
    # Median filer window size
    MED_W: int = 3

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

    def filter_frame(self, img_path: str) -> np.ndarray:
        pass

