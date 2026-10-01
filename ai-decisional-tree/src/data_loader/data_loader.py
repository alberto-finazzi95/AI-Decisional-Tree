import src.common as cm
import src.config_parser as cp


class DataLoader:
    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
    ):
        self._folder_manager: cm.FolderManager  = folder_manager
        self._config_parser: cp.ConfigParser    = config_parser

        # General configuration parameters
        self._set_configuration()
        self._create_folders()

    def _set_configuration(self):
        # Set configuration parameters for data loading
        self._dataset_name: str = self._config_parser.dataset_name
        self._dataset_download_path: str = self._config_parser.dataset_download_path
        self._dataset_extract_path: str = self._config_parser.dataset_extract_path

    def _create_folders(self):
        # Create necessary folders for data loading
        self._folder_manager.create_folder(self._dataset_download_path)
        self._folder_manager.create_folder(self._dataset_extract_path)

    def load_data(self):
        # Implement the logic to load data from the specified path
        pass