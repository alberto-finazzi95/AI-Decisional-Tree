import numpy as np
import matplotlib.pyplot as plt

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

    def plot_tac(self, patient_img_path: str):
        # TODO: Implement the logic to read the patient image data and plot the TAC (Time-Activity Curve)
        pass
