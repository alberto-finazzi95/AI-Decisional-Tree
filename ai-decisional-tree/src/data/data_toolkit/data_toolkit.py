import src.common as cm
import src.config_parser as cp
import src.data.data_plotter as dp
import src.data.data_loader as dl
import src.data.data_analyzer as da


class DataToolkit:
    def __init__(
            self,
            os_manager: cm.OsManager,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
    ):
        # Load data using the DataLoader class
        self.data_loader: dl.DataLoader = dl.DataLoader(
            folder_manager=folder_manager,
            config_parser=config_parser,
            os_manager=os_manager,
        )

        self.data_plotter: dp.DataPlotter = dp.DataPlotter(
            folder_manager=folder_manager,
            config_parser=config_parser,
            os_manager=os_manager
        )

        self.data_analyzer: da.DataAnalyzer = da.DataAnalyzer(
            folder_manager=folder_manager,
            config_parser=config_parser,
            os_manager=os_manager
        )

        # Add to a list the data objects
        self._data_obj_tuple: tuple = (
            self.data_loader,
            self.data_plotter,
            self.data_analyzer,
        )
        # Config parser and folder manager instances
        self.config_parser: cp.ConfigParser = config_parser
        self.folder_manager: cm.FolderManager = folder_manager

    def reset_img_manager_dict(self):
        for data_obj in self._data_obj_tuple:
            data_obj.clean_img_manager_dict()
