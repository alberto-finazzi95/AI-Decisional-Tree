"""Statistical summaries calculated from a study catalog."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StudyStatistics:
    """Summary statistics for clinical and outcome features in a study catalog."""

    lethality_percentage: float
    sex_distribution: dict[str, float]
    sex_missing_percentage: float
    age_mean: float
    age_std: float
    nihss_mean: float
    nihss_std: float
    nihss_missing_percentage: float
    time_distribution: dict[str, float]
    time_missing_percentage: float
    dsa_positive_percentage: float
    dsa_missing_percentage: float
