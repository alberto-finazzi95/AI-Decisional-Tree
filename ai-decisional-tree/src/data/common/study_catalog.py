"""
@brief Build and query study metadata from a dataset summary table.
"""

import pandas as pd

import src.data.common.data_structures as ds
import src.data.common.exceptions as ex


class StudyCatalog:
    """
    @brief Index studies from a summary DataFrame and provide study lookups.

    Provides study-oriented access to the dataset summary DataFrame.
    """

    def __init__(self, summary: pd.DataFrame):
        """
        @brief Index study metadata from the supplied summary DataFrame.
        @param summary: Dataset summary DataFrame.
        """
        self._studies: dict[str, ds.Study] = {
            row[ds.Feature.NAME]: ds.Study(
                study_id=row[ds.Feature.NAME],
                manufacturer=row.get(ds.Feature.MANUFACTURER, ""),
                model=row.get(ds.Feature.MODEL, ""),
                device=row.get(ds.Feature.DEVICE, ""),
                age=row.get(ds.Feature.AGE, -1),
                sex=row.get(ds.Feature.SEX, ""),
                nihss=row.get(ds.Feature.NIHSS, -1),
                time=row.get(ds.Feature.TIME, ""),
                lethality=row.get(ds.Feature.LETHALITY, ""),
                path=row.get(ds.Feature.PATH, ""),
                num_subfolders=row.get(ds.Feature.NUM_SUB, 0),
                subfolders=self._import_subfolders(row.get(ds.Feature.SUBFOLDERS, "")),
            )
            for _, row in summary.iterrows()
        }

    @staticmethod
    def _import_subfolders(subfolders_str: str) -> tuple[str, ...]:
        """
        @brief Parse a comma-separated subfolder field into a tuple of names.
        @param subfolders_str: Comma-separated subfolder names; may be empty.
        @return: The trimmed subfolder names, or an empty tuple.
        """
        return tuple(folder.strip() for folder in subfolders_str.split(",")) if subfolders_str else ()

    def get_subfolders(self, study_id: str) -> tuple[str, ...]:
        """
        @brief Return the frame subfolder names recorded for a study.
        @param study_id: Unique study identifier.
        @return: The tuple[str, ...] produced by this operation.
        """
        study: ds.Study = self.get_study(study_id)
        return study.subfolders

    def get_abs_subfolders(self, study_id: str) -> tuple[str, ...]:
        """
        @brief Return absolute paths to a study's recorded subfolders.
        @param study_id: Unique study identifier.
        @return: The tuple[str, ...] produced by this operation.
        """
        study: ds.Study = self.get_study(study_id)
        return study.abs_subfolders

    def get_path(self, study_id: str) -> str:
        """
        @brief Return the recorded filesystem path for a study.
        @param study_id: Unique study identifier.
        @return: The str produced by this operation.
        """
        study: ds.Study = self.get_study(study_id)
        return study.path

    def get_study(self, study_id: str) -> ds.Study:
        """
        @brief Return the study identified by its unique ID.

        Get one study by its unique identifier.
        @param study_id: Unique study identifier.
        @return: The ds.Study produced by this operation.
        @throws StudyNotFoundError: If the operation encounters this error.
        """
        try:
            return self._studies[study_id]
        except KeyError as err:
            raise ex.StudyNotFoundError(study_id) from err

    @property
    def studies(self) -> tuple[ds.Study, ...]:
        """
        @brief Return all studies indexed by this catalog.

        Return all studies.
        @return: The tuple[ds.Study, ...] produced by this operation.
        """
        return tuple(self._studies.values())
