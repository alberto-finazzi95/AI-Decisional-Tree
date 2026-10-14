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

        # Config parser and folder manager instances
        self.config_parser: cp.ConfigParser = config_parser
        self.folder_manager: cm.FolderManager = folder_manager
