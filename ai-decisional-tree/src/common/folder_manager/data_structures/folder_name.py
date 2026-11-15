"""
@brief Define canonical directory names used by the application.
"""
from enum import StrEnum


class FolderName(StrEnum):
    """
    @brief Canonical directory names used by the application.
    """
    CONFIG = "config"
    DATASET = "dataset"
    IMAGE = "image"
    VIDEO = "video"
    IMAGE_FLT = "image filtered"
    VIDEO_FLT = "video filtered"
    VOLUMES = "volumes"
