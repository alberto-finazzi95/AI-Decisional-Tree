from pathlib import Path

from dataclasses import dataclass


@dataclass(frozen=True)
class Study:
    """Study metadata and its location within a dataset split."""
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
        return tuple(str(Path(self.path) / subfolder) for subfolder in self.subfolders)
