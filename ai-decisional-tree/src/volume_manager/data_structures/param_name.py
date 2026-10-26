from enum import StrEnum


def pixel_name(x: int, y: int, z: int) -> str:
    return f"pixel_z{z}_y{y}_x{x}"


class ParamEnum(StrEnum):
    META_NORM =         "metadata_z_norm"
    STAT_MEAN_3D =      "stat_local_mean_3d"
    STAT_MEAN_STD =     "stat_local_std_3d"
    TARGET =            "target_class"
