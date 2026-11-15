"""
@brief Load image and mask matrices and apply image filtering.
"""

from pathlib import Path

import numpy as np
import scipy.ndimage as nimg

import src.common as cm


class ImageManager:
    """
    @brief Load and process image and segmentation-mask matrices for one patient.
    """

    def __init__(self, patient_path: str, folder_manager: cm.FolderManager):
        """
        @brief Load the raw image and segmentation mask for one patient directory.
        @param patient_path: Directory containing the patient image and mask files.
        @param folder_manager: Folder manager used for filesystem operations.
        """
        self._patient_path: str = patient_path
        self._folder_manager: cm.FolderManager = folder_manager
        # Setting the matrices
        self._img_matrix: np.ndarray = np.ndarray([])
        self._img_flt_matrix: np.ndarray = np.ndarray([])
        self._mask_matrix: np.ndarray = np.ndarray([])
        # Load the raw matrices
        self.load_matrices()

    @property
    def img_matrix(self) -> np.ndarray:
        """
        @brief Return the raw image matrix.
        @return: The np.ndarray produced by this operation.
        """
        return self._img_matrix

    @property
    def img_flt_matrix(self) -> np.ndarray:
        """
        @brief Return the filtered image matrix.
        @return: The np.ndarray produced by this operation.
        """
        return self._img_flt_matrix

    @property
    def mask_matrix(self) -> np.ndarray:
        """
        @brief Return the segmentation-mask matrix.
        @return: The np.ndarray produced by this operation.
        """
        return self._mask_matrix

    @staticmethod
    def load_npz_matrix(path: str | Path) -> np.ndarray:
        """
        @brief Load the first array in an NPZ archive as float32.
        @param path: Filesystem path to inspect or process.
        @return: The np.ndarray produced by this operation.
        """
        with np.load(path) as data:
            key = next(iter(data.keys()))
            return data[key].astype(np.float32)

    def compose_path(self, *args: str) -> str:
        """
        @brief Join path components using the configured folder manager.
        @param args: Additional positional arguments.
        @return: The str produced by this operation.
        """
        return self._folder_manager.compose_folders(*args, str_format=True)

    def load_matrices(self):
        """
        @brief Load raw image and mask arrays from the patient directory.
        """
        img_path: str = self.compose_path(self._patient_path, cm.ImageFileType.IMG)
        mask_path: str = self.compose_path(self._patient_path, cm.ImageFileType.MASK)

        # Load the image and mask data
        self._img_matrix: np.ndarray = self.load_npz_matrix(img_path)
        self._mask_matrix: np.ndarray = self.load_npz_matrix(mask_path)

    def filer_img(self, bw_wl: float, bw_ww: float, m_w: int):
        # First brain window
        """
        @brief Apply brain windowing and median filtering to the raw image.
        @param bw_wl: Lower brain-window intensity bound.
        @param bw_ww: Upper brain-window intensity bound.
        @param m_w: Median-filter window size.
        """
        img_bw: np.ndarray = self.brain_window(self._img_matrix, bw_wl, bw_ww)
        # Median filter
        self._img_flt_matrix = self.median_filter(img_bw, m_w)

    @staticmethod
    def brain_window(img_hu: np.ndarray, br_w_inf: float, br_w_sup: float) -> np.ndarray:
        # Filtering
        """
        @brief Clip image intensities to the supplied bounds and normalize them.
        @param img_hu: Image intensities in Hounsfield units.
        @param br_w_inf: Lower brain-window intensity bound.
        @param br_w_sup: Upper brain-window intensity bound.
        @return: The np.ndarray produced by this operation.
        """
        windowed: np.ndarray = np.clip(img_hu, br_w_inf, br_w_sup)
        # Normalization
        normalized: np.ndarray = (windowed - br_w_inf) / (br_w_sup - br_w_inf)
        return normalized

    @staticmethod
    def median_filter(img: np.ndarray, window_l: int) -> np.ndarray:
        """
        @brief Apply a multidimensional median filter with the given window size.
        @param img: Image data or image-output flag, as appropriate.
        @param window_l: Median-filter window size.
        @return: The np.ndarray produced by this operation.
        """
        return nimg.median_filter(img, window_l)

    def save_filter_img(self):
        """
        @brief Save the filtered image matrix as a compressed NPZ archive if absent.
        """
        img_flt_path: str = self.compose_path(self._patient_path, cm.ImageFileType.IMG_FLT)
        if self._folder_manager.file_exists(img_flt_path):
            print(f"File {img_flt_path} already exists, so it is not necessary to reload the data")
            return
        np.savez_compressed(img_flt_path, img_flt=self._img_flt_matrix)
