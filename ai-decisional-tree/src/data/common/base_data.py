from abc import ABC

import numpy as np

import src.common as cm
import src.config_parser as cp
import src.image_manager.image_manager as im


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

        # Variables
        self._img_manager_dict: dict[str, im.ImageManager] = {}

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
        self._summary_csv_path: str = self._folder_manager.get_file_path(
            file_name=cm.FileName.SUMMARY_CSV,
            folder_name=self._dataset_folder,
            str_format=True
        )

    def folder_exists(self, folder_path: str) -> bool:
        return self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path)

    def compose_path(self, *args: str) -> str:
        return self._folder_manager.compose_folders(*args, str_format=True)

    def get_img_manager(self, patient_img_path: str) -> im.ImageManager:
        if patient_img_path not in self._img_manager_dict:
            # Create the object to manage images
            img_manager: im.ImageManager = im.ImageManager(patient_img_path, self._folder_manager)
            # Store in the dictionary
            self._img_manager_dict[patient_img_path] = img_manager
        return self._img_manager_dict[patient_img_path]

    def clean_img_manager_dict(self):
        self._img_manager_dict.clear()

    def load_matrices(self, patient_img_path: str) -> tuple[np.ndarray, np.ndarray]:
        img_manager: im.ImageManager = self.get_img_manager(patient_img_path)
        # Load the matrices
        return img_manager.img_matrix, img_manager.mask_matrix

    def load_filtered_matrices(self, patient_img_path: str) -> tuple[np.ndarray, np.ndarray]:
        img_manager: im.ImageManager = self.get_img_manager(patient_img_path)
        # Load the matrices
        return img_manager.img_flt_matrix, img_manager.mask_matrix

    def path_exists(self, path: str) -> bool:
        """
        Checks if a given path exists.

        Args:
            path (str): The path to check.
        """
        return self._folder_manager.folder_exists(path)

    def file_exists(self, path: str) -> bool:
        """
        Checks if a given path exists.

        Args:
            path (str): The path to check.
        """
        return self._folder_manager.file_exists(path)

    def create_folder(self, folder_path: str) -> None:
        """
        Creates a folder at the specified path.

        Args:
            folder_path (str): The path where the folder should be created.
        """
        self._folder_manager.create_folder(folder_path)

    def _create_not_existing_folder(self, folder_path: str):
        if not self.path_exists(folder_path):
            print(f"Path '{folder_path}' does not exist. Creating...")
            self.create_folder(folder_path)
