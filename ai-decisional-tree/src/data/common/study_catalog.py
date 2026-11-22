"""
@brief Build and query study metadata from a dataset summary table.
"""

import numpy as np
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
        # Number of studies indexed by this catalog
        self._num_studies: int = len(self._studies)
        # Get the percentage of lethality values that are true or false
        self._lethality_percentage: float = self._calculate_lethality_percentage(summary)
        # Sex and age distributions
        self._sex_distribution, self._sex_missing_count = self._set_sex_distribution(summary)
        self._age_distribution: tuple[float, float] = self._set_age_distribution(summary)

    def get_lethality_percentage(self) -> float:
        """
        @brief Return the percentage of lethality values of the study catalog.
        @return: The float produced by this operation."""
        return self._lethality_percentage

    def get_sex_distribution(self) -> dict[str, float]:
        """
        @brief Return the distribution of sex values in the study catalog.
        @return: The dict[str, float] produced by this operation.
        """
        return self._sex_distribution

    def get_sex_missing_count(self) -> float:
        """
        @brief Return the number of missing sex values in the study catalog.
        @return: The number of missing sex values.
        """
        return self._sex_missing_count

    def get_age_distribution(self) -> tuple[float, float]:
        """
        @brief Return the distribution of age values in the study catalog.
        @return: The tuple[float, float] produced by this operation.
        """
        return self._age_distribution

    def _calculate_lethality_percentage(self, df: pd.DataFrame) -> float:
        """
        @brief Calculate the percentage of lethality values that are true or false.
        @param df: Dataset summary DataFrame.
        @return: The float produced by this operation.
        """
        lethality: float = self._percentage(df[ds.Feature.LETHALITY].sum())
        return self._round_value(lethality)

    def _set_sex_distribution(self, df: pd.DataFrame) -> tuple[dict[str, float], float]:
        """
        @brief Calculate the distribution of sex values in the dataset summary.
        @param df: Dataset summary DataFrame.
        @return: The sex distribution percentages and number of missing values.
        """
        sex_values: pd.Series = df[ds.Feature.SEX]
        missing_sex_count: float = self._percentage(sex_values.isna().sum())
        distribution: dict[str, float] = {
            sex: self._round_value(self._percentage(count)) for sex, count in sex_values.value_counts().items()
        }
        return distribution, self._round_value(missing_sex_count)

    def _set_age_distribution(self, df: pd.DataFrame) -> tuple[float, float]:
        """
        @brief Calculate the distribution of age values in the dataset summary.
        @param df: Dataset summary DataFrame.
        @return: A tuple containing the mean and standard deviation of age values.
        """
        age_values: pd.Series = df[ds.Feature.AGE]
        mean_age: float = np.mean(age_values)
        std_age: float = np.std(age_values)
        return self._round_value(mean_age), self._round_value(std_age)

    @staticmethod
    def _round_value(value: float, decimals: int = 2) -> float:
        """
        @brief Round a float value to the specified number of decimal places.
        @param value: The float value to round.
        @param decimals: The number of decimal places to round to (default is 2).
        @return: The rounded float value.
        """
        return np.around(value, decimals)

    def _percentage(self, value: float) -> float:
        """
        @brief Calculate the percentage of a value relative to a total.
        @param value: The value to calculate the percentage for.
        @return: The calculated percentage as a float.
        """
        return (value / self._num_studies) * 100.0

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
