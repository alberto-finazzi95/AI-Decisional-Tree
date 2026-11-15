"""
@brief Define canonical file names used by the folder manager.
"""
from enum import StrEnum


class FileName(StrEnum):
    """
    @brief Canonical file names used by configuration and dataset helpers.
    """
    CONFIG = "config.ini"
    SUMMARY_CSV = "summary.csv"
