import pandas as pd

import src.data.common.exceptions as ex
import src.data.common.data_structures as ds


class StudyCatalog:
    """Provides study-oriented access to the dataset summary DataFrame."""

    def __init__(self, summary: pd.DataFrame):
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
        """Return the subfolders for a given study."""
        return tuple(subfolders_str.split(",")) if subfolders_str else ()


    def get_subfolders(self, study_id: str) -> tuple[str, ...]:
        study: ds.Study = self.get_study(study_id)
        return study.subfolders

    def get_study(self, study_id: str) -> ds.Study:
        """Get one study by its unique identifier."""
        try:
            return self._studies[study_id]
        except KeyError:
            raise ex.StudyNotFoundError(study_id)

    @property
    def studies(self) -> tuple[ds.Study, ...]:
        """Return all studies."""
        return tuple(self._studies.values())
