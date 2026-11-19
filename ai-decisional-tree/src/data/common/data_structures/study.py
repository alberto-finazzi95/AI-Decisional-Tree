"""
@brief Represent immutable metadata and paths for a dataset study.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Study:
    """
    @brief Immutable metadata and directory information for one study.

    Study metadata and its location within a dataset split.
    """

    study_id: str
    manufacturer: str
    model: str
    device: str
    age: int
    sex: str
    nihss: int
    time: str
    lethality: str
    path: str
    num_subfolders: int
    subfolders: tuple[str, ...] = ()

    @property
    def abs_subfolders(self):
        """
        @brief Return full paths for the study's subfolders.
        @return: The value produced by this operation.
        """
        return tuple(str(Path(self.path) / subfolder) for subfolder in self.subfolders)
