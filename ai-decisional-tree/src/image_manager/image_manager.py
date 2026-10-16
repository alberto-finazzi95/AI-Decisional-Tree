from pathlib import Path

import numpy as np
import scipy.ndimage as nimg

import src.common as cm
import src.data.data_plotter.data_structures as dps


class ImageManager:
    def __init__(self, patient_path: str, folder_manager: cm.FolderManager):
        self._patient_path: str = patient_path
        self._folder_manager: cm.FolderManager = folder_manager

    @staticmethod
    def load_npz_matrix(path: str | Path) -> np.ndarray:
        with np.load(path) as data:
            key = next(iter(data.keys()))
            return data[key].astype(np.float32)

    def compose_path(self, *args: str) -> str:
        return self._folder_manager.compose_folders(*args, str_format=True)

    def load_matrices(self):
        img_path: str    = self.compose_path(self._patient_path, dps.ImageFileType.IMG)
        mask_path: str   = self.compose_path(self._patient_path, dps.ImageFileType.MASK)

        # Load the image and mask data
        img_matrix: np.ndarray      = self.load_npz_matrix(img_path)
        mask_matrix: np.ndarray     = self.load_npz_matrix(mask_path)

        return img_matrix, mask_matrix

    @staticmethod
    def brain_window(img_hu: np.ndarray, wl: float , ww: float ) -> np.ndarray:
        # Setting brain window parameters
        min_hu: float = wl - (ww / 2.0)
        max_hu: float = wl + (ww / 2.0)
        # Filtering
        windowed: np.ndarray  = np.clip(img_hu, min_hu, max_hu)
        # Normalization
        normalized: np.ndarray  = (windowed - min_hu) / (max_hu - min_hu)
        return normalized

    @staticmethod
    def median_filter(img: np.ndarray, window_l: int) -> np.ndarray:
        return nimg.median_filter(img, window_l)