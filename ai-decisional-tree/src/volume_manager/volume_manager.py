import numpy as np
import pandas as pd

import scipy.ndimage as ndimg

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

    @property
    def valid_pixel(self) -> np.ndarray:
        return (self._vol_img[1:-1, 1:-1, 1:-1] != 0) \
                | (self._vol_img[:-2, 1:-1, 1:-1] != 0) \
                | (self._vol_img[2:, 1:-1, 1:-1] != 0)


    def build(self):
        # Creating the array matrices
        self._vol_img = np.array(self._img_list)
        self._vol_msk = np.array(self._msk_list)

        # 3D NumPy array with axes: (Z=slice, Y=height, X=width)
        self.z, self.y, self.x = self._vol_img.shape

        # Extracting only one time the matrices
        num_slices: int = self.num_slices
        mean_volume: np.ndarray = self.mean_volume
        std_volume: np.ndarray = self.std_volume

        # Consider only non-empty voxels or voxels adjacent to non-empty ones.
        # This avoids spinning through a huge number of background-only voxels.
        z_idx, y_idx, x_idx = np.nonzero(self.valid_pixel)

        for i in range(len(z_idx)):
            z: int = int(z_idx[i] + 1)
            y: int = int(y_idx[i] + 1)
            x: int = int(x_idx[i] + 1)

            # Store values into the record
            volume_record = vr.VolumeRecord(
                metadata_z_norm= z / num_slices,
                stat_local_mean_3d= float(mean_volume[z, y, x]),
                stat_local_std_3d= float(std_volume[z, y, x]),
                target_class= int(self._vol_msk[z, y, x]),
            )
            # Extra info of the neighborhood
            self.pixel_neighborhood(x, y, z, volume_record)
            # Store in the list the record
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
