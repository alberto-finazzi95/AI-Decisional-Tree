"""
@brief Define raw and filtered image processing states.
"""
from enum import Enum


class ImageState(Enum):
    """
    @brief Image processing modes supported by the pipeline.
    """
    RAW = 0
    FILTER = 1
