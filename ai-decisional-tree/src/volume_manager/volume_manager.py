import numpy as np
import pandas as pd
import scipy.ndimage as ndimg
from numba import njit

import src.volume_manager.data_structures as ds
import src.volume_manager.volume_record as vr


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
        self._records: list[vr.VolumeRecord] = []

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
        self._records.clear()

    @property
    def vol_img(self) -> np.ndarray:
        return self._vol_img

    @property
    def vol_msk(self) -> np.ndarray:
        return self._vol_msk

    @property
    def records(self) -> list[vr.VolumeRecord]:
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
        z_idx, y_idx, x_idx, means, stds, labels = _extract_valid_voxels(
            self._vol_img,
            self._vol_msk,
            mean_volume,
            std_volume,
        )

        # Reset the record list before filling it with the new patient volume.
        # This prevents stale records from previous builds from remaining in memory.
        self._records = []

        # Rebuild one VolumeRecord per valid voxel.
        # Each record contains the normalized z coordinate, local stats, target class,
        # and the surrounding 3x3x3 neighborhood values used as features.
        for i in range(len(z_idx)):
            z: int = int(z_idx[i])
            y: int = int(y_idx[i])
            x: int = int(x_idx[i])

            volume_record: vr.VolumeRecord = vr.VolumeRecord(
                metadata_z_norm=z / num_slices,
                stat_local_mean_3d=float(means[i]),
                stat_local_std_3d=float(stds[i]),
                target_class=int(labels[i]),
            )

            # Attach the 27-neighborhood values around this voxel.
            # This adds contextual information for classification/regression features.
            self.pixel_neighborhood(x, y, z, volume_record)

            # Save the completed record in the final dataset for this volume.
            self._records.append(volume_record)

    def pixel_neighborhood(
            self,
            x: int,
            y: int,
            z: int,
            volume_record: vr.VolumeRecord):
        # Dynamically extract all 27 pixels from the surrounding 3x3x3 cube
        # dz=-1 (previous slice), dz=0 (current slice), dz=1 (next slice)
        for dz in self.WINDOW_RANGE:
            for dy in self.WINDOW_RANGE:
                for dx in self.WINDOW_RANGE:
                    # Creating the pixel
                    pixel: ds.Pixel = ds.Pixel(x=dx, y=dy, z=dz)
                    # Getting the value
                    value: float = self._vol_img[z + dz, y + dy, x + dx]
                    # Storing in the record
                    volume_record.add_pixel(pixel, value)

    def to_dataframe(self) -> pd.DataFrame:
        # Convert into a list of dictionaries
        total_data_records: list = [record.to_dict() for record in self._records]
        # Return the dataframe
        return pd.DataFrame(total_data_records)


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
