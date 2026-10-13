from enum import StrEnum


class Feature(StrEnum):
    """Enum class for feature names used in the dataset."""

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
