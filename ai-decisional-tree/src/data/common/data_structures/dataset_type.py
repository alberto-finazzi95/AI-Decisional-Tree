"""
@brief Define the supported dataset splits.
"""
from enum import StrEnum


class DatasetType(StrEnum):
    """
    @brief Supported dataset split identifiers.
    """
    TRAIN = "train"
    VALIDATION = "val"
    TEST = "test"
