"""
@brief Define column names used in dataset summary tables.
"""

from enum import StrEnum


class Feature(StrEnum):
    """
    @brief Names and meanings of columns in the study summary.

    Source metadata:
        NAME: Unique study identifier (a DICOM Study Instance UID in the source dataset).
        MANUFACTURER: Manufacturer of the imaging equipment.
        MODEL: Imaging equipment model.
        DEVICE: Combined imaging device name, typically manufacturer and model.
        AGE: Patient age, in years.
        SEX: Patient sex as recorded in the source metadata.
        DSA: Whether digital subtraction angiography is recorded for the study.
        NIHSS: National Institutes of Health Stroke Scale score, measuring stroke
            severity; higher scores indicate more severe neurological impairment.
        TIME: Recorded time value or range associated with the study. It remains a
            string because it may represent either one value or a range.
        LETHALITY: Boolean outcome label indicating whether the study is marked as lethal.
        PART: Dataset split to which the study belongs (train, validation, or test).

    Derived or processing metadata:
        PATH: Filesystem path to the study directory.
        NUM_SUB: Number of frame subfolders found for the study.
        SUBFOLDERS: Names of the frame subfolders found for the study.
        TIME_INF: Numeric lower bound parsed from TIME.
        TIME_SUP: Numeric upper bound parsed from TIME.

    Enum members provide the corresponding column names.
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
