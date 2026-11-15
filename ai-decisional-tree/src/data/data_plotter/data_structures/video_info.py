"""
@brief Define the encoding settings used for generated videos.
"""

from typing import Final, final


@final
class VideoInfo:
    """
    @brief Video encoding constants used when opening a video writer.
    """

    fps: Final[int] = 10
    format: Final[str] = "FFMPEG"
    mode: Final[str] = "I"
