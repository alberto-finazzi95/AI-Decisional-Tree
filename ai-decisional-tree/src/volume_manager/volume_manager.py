import numpy as np
import pandas as pd
import scipy.ndimage as ndimg
from numba import njit

import src.volume_manager.data_structures as ds


class VolumeManager:
    # Window len for the uniform filter
    UNIFORM_FILTER_W: int = 3
    # Cube 3x3x3 of the pixel
    # Range for the neighborhood
    WINDOW_RANGE: tuple[int, ...] = (-1, 0, 1)

    def __init__(self):
        # List of tacs
        self._img_list: list[np.ndarray] = []
        self._msk_list: list[np.ndarray] = []
        # Volume
        self._vol_img: np.ndarray = np.array([])
        self._vol_msk: np.ndarray = np.array([])
        # Dimensions
        self.x: int = 0
        self.y: int = 0
        self.z: int = 0
        # The elaborated data
        self._records: pd.DataFrame = pd.DataFrame()

    def clean(self):
        # List of tacs
        self._img_list = []
        self._msk_list = []
        # Volume
        self._vol_img = np.array([])
        self._vol_msk = np.array([])
        # Dimensions
        self.x = 0
        self.y = 0
        self.z = 0
        # The elaborated data
        self._records = pd.DataFrame()

    @property
    def vol_img(self) -> np.ndarray:
        return self._vol_img

    @property
    def vol_msk(self) -> np.ndarray:
        return self._vol_msk

    @property
    def records(self) -> pd.DataFrame:
        return self._records

    def add_img(self, img_matrix: np.ndarray):
        self._img_list.append(img_matrix)

    def add_msk(self, msk_matrix: np.ndarray):
        self._msk_list.append(msk_matrix)

    def clean_vol_img(self):
        """Clear the entire CT image volume and release memory."""
        self._img_list.clear()
        self._vol_img = np.array([])
        # Resetting the dimensions
        self.x = 0
        self.y = 0
        self.z = 0

    def clean_vol_msk(self):
        """Clear the entire clinical mask volume."""
        self._msk_list.clear()
        self._vol_msk = np.array([])

    def reset_all(self):
        """Reset the manager for a new patient."""
        self.clean_vol_img()
        self.clean_vol_msk()

    def uniform_filter(self, img: np.ndarray) -> np.ndarray:
        return ndimg.uniform_filter(img, size=self.UNIFORM_FILTER_W)

    @property
    def mean_volume(self) -> np.ndarray:
        '''
            Pre-compute the 3D statistical matrices over the entire volume for maximum speed
            A 3x3x3 uniform filter computes the local mean in a cube around each pixel
        Returns: mean volume

        '''
        return self.uniform_filter(self._vol_img)

    @property
    def mean_sq_volume(self) -> np.ndarray:
        return self.uniform_filter(self._vol_img ** 2)

    # Fast calculation of the local 3D standard deviation: sqrt(E[X^2] - (E[X])^2)
    @property
    def std_volume(self) -> np.ndarray:
        return np.sqrt(np.clip(self.mean_sq_volume - self.mean_volume ** 2, 0, None))

    @property
    def num_slices(self) -> int:
        return len(self._img_list)

    def build(self):
                # Rebuild the full 3D volume from the per-slice CT images and masks.
        # This is the compact representation used for all subsequent processing.
        self._vol_img = np.array(self._img_list)
        self._vol_msk = np.array(self._msk_list)

        # Store the volume dimensions with axes ordered as (Z, Y, X).
        # These values are used later as metadata and for neighborhood access.
        self.z, self.y, self.x = self._vol_img.shape

        # Compute local statistics once: mean and std over the 3D neighborhood.
        # Doing it once avoids repeating the expensive filter for each voxel.
        num_slices: int = self.num_slices
        mean_volume: np.ndarray = self.mean_volume
        std_volume: np.ndarray = self.std_volume

        # Keep only the voxels that are relevant for training/inference:
        # non-empty voxels or voxels adjacent to non-empty ones.
        # This removes a large amount of background-only data from the pipeline.
        z_idx: np.ndarray
        y_idx: np.ndarray
        x_idx: np.ndarray
        means: np.ndarray
        stds: np.ndarray
        labels: np.ndarray
        z_idx, y_idx, x_idx, means, stds, labels = _extract_valid_voxels(
            self._vol_img,
            self._vol_msk,
            mean_volume,
            std_volume,
        )

        # Reset the record list before filling it with the new patient volume.
        # This prevents stale records from previous builds from remaining in memory.
        self._records = pd.DataFrame()

        # Convert to fixed-size integer arrays to improve indexing efficiency.
        z_idx = z_idx.astype(np.int32)
        y_idx = y_idx.astype(np.int32)
        x_idx = x_idx.astype(np.int32)

        # Precompute all 27 neighborhood offsets used by the 3x3x3 cube.
        # Each tuple represents the relative displacement in (z, y, x) coordinates.
        offsets: list[tuple[int, int, int]] = [
            (dz, dy, dx)
            for dz in self.WINDOW_RANGE
            for dy in self.WINDOW_RANGE
            for dx in self.WINDOW_RANGE
        ]

        # neighborhood shape: (N_valid_voxels, 27)
        # We fill one column per offset so we avoid the Python-level for-loop over voxels.
        neighborhood: np.ndarray = np.empty((len(z_idx), len(offsets)), dtype=np.float32)
        for i, (dz, dy, dx) in enumerate(offsets):
            neighborhood[:, i] = self._vol_img[z_idx + dz, y_idx + dy, x_idx + dx]

        # Build the DataFrame columns directly as NumPy arrays.
        # This keeps the output compatible with downstream code while avoiding per-voxel
        # Python object creation.
        data: dict[str, np.ndarray] = {
            ds.ParamEnum.META_NORM: z_idx.astype(np.float32) / num_slices,
            ds.ParamEnum.STAT_MEAN_3D: means.astype(np.float32),
            ds.ParamEnum.STAT_MEAN_STD: stds.astype(np.float32),
            ds.ParamEnum.TARGET: labels.astype(np.int16),
        }

        for i, (dz, dy, dx) in enumerate(offsets):
            data[f"pixel_x_{dx}_y_{dy}_z_{dz}"] = neighborhood[:, i]

        # Convert the columnar representation to row-oriented records in one final pass.
        self._records = pd.DataFrame(data)


@njit(cache=True)
def _extract_valid_voxels(
    vol_img: np.ndarray,
    mask: np.ndarray,
    mean_vol: np.ndarray,
    std_vol: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract valid voxels without materializing a giant temporary array.

    This version is optimized for throughput:
    - avoids the Python-level triple loop by expressing the validity condition as a
      boolean mask and then extracting the coordinates with np.nonzero;
    - keeps only the voxels that are not empty or adjacent along the z axis;
    - reads the local statistics and mask labels in a single pass.
    """
    # Validity condition: keep voxels that are non-zero or have a non-zero neighbor
    # in the previous/next slice. This matches the original semantics while using a
    # vectorized mask for better cache locality and lower branch overhead.
    valid_mask: np.ndarray = (
        (vol_img[1:-1, 1:-1, 1:-1] != 0)
        | (vol_img[:-2, 1:-1, 1:-1] != 0)
        | (vol_img[2:, 1:-1, 1:-1] != 0)
    )

    z_valid: np.ndarray
    y_valid: np.ndarray
    x_valid: np.ndarray
    z_valid, y_valid, x_valid = np.nonzero(valid_mask)

    # Re-map the sliced indices back to the original volume coordinates.
    z_idx: np.ndarray = z_valid + 1
    y_idx: np.ndarray = y_valid + 1
    x_idx: np.ndarray = x_valid + 1

    # Read statistics and labels once for the selected voxels.
    means: np.ndarray = mean_vol[z_idx, y_idx, x_idx]
    stds: np.ndarray = std_vol[z_idx, y_idx, x_idx]
    labels: np.ndarray = mask[z_idx, y_idx, x_idx]

    return z_idx, y_idx, x_idx, means, stds, labels
