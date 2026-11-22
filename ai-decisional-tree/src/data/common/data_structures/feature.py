"""
@brief Define column names used in dataset summary tables.
"""

from enum import StrEnum


class Feature(StrEnum):
    """
    @brief Dataset summary column names.

    Enum class for feature names used in the dataset.
    """

    # Define feature names as enum members
    NAME = "name"
    MANUFACTURER = "manufacturer"
    MODEL = "model"
    DEVICE = "device"
    AGE = "age"
    SEX = "sex"
    DSA = "dsa"
    NIHSS = "nihss"
    TIME = "time"
    LETHALITY = "lethality"
    PART = "part"
    # Feature customized
    PATH = "path"
    NUM_SUB = "num subfolders"
    SUBFOLDERS = "subfolders"
    TIME_INF = "time_inf"
    TIME_SUP = "time_sup"


OUT_FEATURE: str = Feature.LETHALITY

MAIN_FEATURES: tuple[Feature, ...] = (
    Feature.AGE,
    Feature.SEX,
    Feature.DSA,
    Feature.NIHSS,
    Feature.TIME_INF,
    Feature.TIME_SUP,
    Feature.LETHALITY,
)

ALL_FEATURES: tuple[Feature, ...] = (
    Feature.MANUFACTURER,
    Feature.MODEL,
    Feature.DEVICE,
) + MAIN_FEATURES
