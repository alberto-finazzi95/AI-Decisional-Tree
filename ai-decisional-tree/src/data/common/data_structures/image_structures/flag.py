"""
@brief Represent configuration flags for image and video output.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Flag:
    """
    @brief Boolean settings controlling image and video output.
    """
    img: bool
    video: bool

    def all_media_disabled(self) -> bool:
        """
        @brief Return whether both image and video output are disabled.
        @return: The bool produced by this operation.
        """
        return (not self.img) and (not self.video)
