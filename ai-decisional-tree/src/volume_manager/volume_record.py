from dataclasses import dataclass

import src.volume_manager.data_structures as ds


@dataclass
class VolumeRecord:
    # Spatial height information within the skull (normalized 0-1)
    metadata_z_norm: float
    # Statistic Volumetric Feature (3D) of the cube
    stat_local_mean_3d: float
    stat_local_std_3d: float
    # Clinical target
    target_class: float

    def __post_init__(self):
        self.cube_neighborhood: dict[ds.Pixel, float] = {}

    def add_pixel(self, pixel: ds.Pixel, value: float):
        self.cube_neighborhood[pixel] = value

    def to_dict(self) -> dict:
        return {
            ds.ParamEnum.META_NORM: self.metadata_z_norm,
            ds.ParamEnum.STAT_MEAN_3D: self.stat_local_mean_3d,
            ds.ParamEnum.STAT_MEAN_STD: self.stat_local_std_3d,
            ds.ParamEnum.TARGET: self.target_class,
        } | {
            pixel.name: val
            for pixel, val in self.cube_neighborhood.items()
        }
