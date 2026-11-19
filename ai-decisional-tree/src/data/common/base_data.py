"""
@brief Provide shared filesystem and image-loading support for data components.
"""

import numpy as np

import src.common as cm
import src.config_parser as cp
import src.image_manager.image_manager as im


class BaseData:
    """
    @brief Shared paths, image-manager caching, and matrix loading for data components.
    """

    def __init__(
        self,
        folder_manager: cm.FolderManager,
        config_parser: cp.ConfigParser,
        os_manager: cm.OsManager | None = None,
    ):
        """
        @brief Initialize shared filesystem and image-loading dependencies and dataset paths.
        @param folder_manager: Folder manager used for filesystem operations.
        @param config_parser: Parser providing dataset and output settings.
        @param os_manager: Optional filesystem-operation implementation.
        """
        self._folder_manager: cm.FolderManager = folder_manager
        self._config_parser: cp.ConfigParser = config_parser
        self._os_manager: cm.OsManager = os_manager if os_manager is not None else cm.OsWrapper()

        # Variables
        self._img_manager_dict: dict[str, im.ImageManager] = {}

        # General settings
        self._set_folders()
        self._set_files()

    def _set_folders(self):
        """
        @brief Resolve the configured dataset output, extraction, and dataset paths.
        """
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
            str_format=True,
        )

    def _set_files(self):
        """
        @brief Resolve the path to the dataset summary CSV file.
        """
        self._summary_csv_path: str = self._folder_manager.get_file_path(
            file_name=cm.FileName.SUMMARY_CSV,
            folder_name=self._dataset_folder,
            str_format=True,
        )

    def folder_exists(self, folder_path: str) -> bool:
        """
        @brief Check whether the supplied path exists and is a directory.
        @param folder_path: Folder path used by this operation.
        @return: The bool produced by this operation.
        """
        return self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path)

    def compose_path(self, *args: str) -> str:
        """
        @brief Join path components using the configured folder manager.
        @param args: Additional positional arguments.
        @return: The str produced by this operation.
        """
        return self._folder_manager.compose_folders(*args, str_format=True)

    def get_img_manager(self, patient_img_path: str) -> im.ImageManager:
        """
        @brief Return the cached image manager for a patient path, creating it if needed.
        @param patient_img_path: Path to a patient frame directory.
        @return: The im.ImageManager produced by this operation.
        """
        if patient_img_path not in self._img_manager_dict:
            # Create the object to manage images
            img_manager: im.ImageManager = im.ImageManager(patient_img_path, self._folder_manager)
            # Store in the dictionary
            self._img_manager_dict[patient_img_path] = img_manager
        return self._img_manager_dict[patient_img_path]

    def clean_img_manager_dict(self):
        """
        @brief Clear cached image-manager instances.
        """
        self._img_manager_dict.clear()

    def load_matrices(self, patient_img_path: str) -> tuple[np.ndarray, np.ndarray]:
        """
        @brief Load and return the raw image and mask matrices for a patient path.
        @param patient_img_path: Path to a patient frame directory.
        @return: The tuple[np.ndarray, np.ndarray] produced by this operation.
        """
        img_manager: im.ImageManager = self.get_img_manager(patient_img_path)
        # Load the matrices
        return img_manager.img_matrix, img_manager.mask_matrix

    def load_filtered_matrices(self, patient_img_path: str) -> tuple[np.ndarray, np.ndarray]:
        """
        @brief Return the filtered image and mask matrices for a patient path.
        @param patient_img_path: Path to a patient frame directory.
        @return: The tuple[np.ndarray, np.ndarray] produced by this operation.
        """
        img_manager: im.ImageManager = self.get_img_manager(patient_img_path)
        # Load the matrices
        return img_manager.img_flt_matrix, img_manager.mask_matrix

    def path_exists(self, path: str) -> bool:
        """
        @brief Check whether the requested directory path exists.


        Checks if a given path exists.

        Args:
            path (str): The path to check.

        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        return self._folder_manager.folder_exists(path)

    def file_exists(self, path: str) -> bool:
        """
        @brief Check whether the requested file path exists.


        Checks if a given path exists.

        Args:
            path (str): The path to check.

        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        return self._folder_manager.file_exists(path)

    def create_folder(self, folder_path: str) -> None:
        """
        @brief Create the requested directory if it is absent.


        Creates a folder at the specified path.

        Args:
            folder_path (str): The path where the folder should be created.

        @param folder_path: Folder path used by this operation.
        """
        self._folder_manager.create_folder(folder_path)

    def _create_not_existing_folder(self, folder_path: str):
        """
        @brief Create the requested directory only when it does not exist.
        @param folder_path: Directory path to check and create.
        """
        if not self.path_exists(folder_path):
            print(f"Path '{folder_path}' does not exist. Creating...")
            self.create_folder(folder_path)
