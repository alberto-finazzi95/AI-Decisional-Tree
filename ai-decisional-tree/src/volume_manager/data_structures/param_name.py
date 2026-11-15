"""
@brief Define names for voxel features and neighborhood columns.
"""
from enum import StrEnum


def pixel_name(x: int, y: int, z: int) -> str:
    """
    @brief Format a voxel-neighborhood column name from its coordinates.
    @param x: Voxel x-coordinate.
    @param y: Voxel y-coordinate.
    @param z: Voxel z-coordinate.
    @return: The str produced by this operation.
    """
    return f"pixel_z{z}_y{y}_x{x}"


class ParamEnum(StrEnum):
    """
    @brief Names of metadata, statistics, and target columns in voxel records.
    """
    META_NORM = "metadata_z_norm"
    STAT_MEAN_3D = "stat_local_mean_3d"
    STAT_MEAN_STD = "stat_local_std_3d"
    TARGET = "target_class"
