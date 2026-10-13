from abc import ABC

import src.common as cm
import src.config_parser as cp


class BaseData(ABC):
    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
            os_manager: cm.OsManager | None = None
    ):
        self._folder_manager: cm.FolderManager = folder_manager
        self._config_parser: cp.ConfigParser = config_parser
        self._os_manager: cm.OsManager = os_manager if os_manager is not None else cm.OsWrapper()

        # General settings
        self._set_folders()
        self._set_files()

    def _set_folders(self):
        self._dataset_output_folder_name: str = self._config_parser.dataset_output_path
        self._dataset_extract_path: str = self._folder_manager.get_folder_path(
            folder_name=self._config_parser.dataset_output_path,
            str_format=True,
        )
        dataset_name: str = self._folder_manager.compose_folders(
            self._config_parser.dataset_output_path,
            cm.FolderName.DATASET,
            str_format=True,
        )
        self._dataset_folder: str = self._folder_manager.get_folder_path(
            folder_name=dataset_name,
            str_format=True
        )

    def _set_files(self):
        self._summary_csv_path: str = self._folder_manager.get_file_path_if_exist(
            file_name=cm.FileName.SUMMARY_CSV,
            folder_name=self._dataset_folder,
            str_format=True
        )

    def folder_exists(self, folder_path: str) -> bool:
        return self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path)