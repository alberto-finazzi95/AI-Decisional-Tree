"""
@brief Define configuration option names used by the parser.
"""

from enum import StrEnum


class Option(StrEnum):
    """
    @brief Configuration option names.
    """

    NAME = "name"
    OUTPUT_PATH = "output_path"
    IMPORT_DATA = "import data"
    SAVE_IMG = "save img"
    SAVE_VIDEO = "save video"
    SAVE_IMG_FILT = "save img filtered"
    SAVE_VIDEO_FILT = "save video filtered"
