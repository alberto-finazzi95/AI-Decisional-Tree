from typing import Final, final


@final
class VideoInfo:
    fps: Final[int] = 10
    format: Final[str] = "FFMPEG"
    mode: Final[str] = "I"
