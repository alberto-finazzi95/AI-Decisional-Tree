"""
@brief Represent immutable metadata and paths for a dataset study.
"""

from dataclasses import dataclass
from pathlib import Path

import src.data.common.data_structures as ds
import src.data.common.data_structures.exceptions as ex

TIME_SEP: str = "-"  # Separator used in time ranges (e.g., "0-6" for 0 to 6 hours)


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

    @property
    def time_range(self) -> ds.TimeRange:
        """
        @brief Return the time range for the study.
        @return: The parsed time range, or None when the value is missing.
        """
        try:
            # Convert each bound to a number; invalid values are reported as an invalid range.
            time: list[float] = [float(x.strip()) for x in self.time.split(TIME_SEP)]
        except ValueError as err:
            raise ex.InvalidTimeRange(self.time) from err

        # A single value is an exact time; two values represent the lower and upper bounds.
        match len(time):
            case 1:
                return ds.TimeRange(time[0], time[0])
            case 2:
                return ds.TimeRange(time[0], time[1])
            case _:
                raise ex.InvalidTimeRange(self.time)
