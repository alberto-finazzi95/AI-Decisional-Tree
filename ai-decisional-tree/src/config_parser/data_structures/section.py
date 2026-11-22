"""
@brief Define configuration section names used by the parser.
"""

from enum import StrEnum


class Section(StrEnum):
    """
    @brief Configuration section names.
    """

    DATASET = "Dataset"
    PHASES = "Phases"
    STORAGE = "Storing data"
