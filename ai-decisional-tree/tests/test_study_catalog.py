import unittest

import numpy as np
import pandas as pd
import src.data.common as dcm
import src.data.common.exceptions as ex


class StudyCatalogTests(unittest.TestCase):
    """Tests conversion of summary rows into studies and lookup of their data."""

    STUDY_ID: str = "study-001"
    SECOND_STUDY_ID: str = "study-002"
    MINIMAL_STUDY_ID: str = "minimal-study"
    MISSING_STUDY_ID: str = "missing-study"
    MANUFACTURER: str = "SIEMENS"
    MODEL: str = "Emotion 16"
    DEVICE: str = "SIEMENS Emotion 16"
    FEMALE: str = "F"
    TIME_RANGE: str = "0-24"
    STUDY_PATH: str = "dataset/train/study-001"
    SUBFOLDERS: tuple[str, ...] = ("00000", "00001")

    def setUp(self):
        """Creates a catalog with one complete study and one without subfolders."""
        # Identifier used by tests for the complete study.
        self.study_id = self.STUDY_ID
        # Each dictionary represents a summary row containing the study fields.
        self.catalog = dcm.StudyCatalog(
            pd.DataFrame(
                [
                    {
                        dcm.Feature.NAME: self.study_id,
                        dcm.Feature.MANUFACTURER: self.MANUFACTURER,
                        dcm.Feature.MODEL: self.MODEL,
                        dcm.Feature.DEVICE: self.DEVICE,
                        dcm.Feature.AGE: 85,
                        dcm.Feature.SEX: self.FEMALE,
                        dcm.Feature.DSA: True,
                        dcm.Feature.NIHSS: 4,
                        dcm.Feature.TIME: self.TIME_RANGE,
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.PATH: self.STUDY_PATH,
                        dcm.Feature.NUM_SUB: 2,
                        dcm.Feature.SUBFOLDERS: ", ".join(self.SUBFOLDERS),
                    },
                    {
                        dcm.Feature.NAME: self.SECOND_STUDY_ID,
                        dcm.Feature.MANUFACTURER: "GE",
                        dcm.Feature.MODEL: "Revolution",
                        dcm.Feature.DEVICE: "GE Revolution",
                        dcm.Feature.AGE: 72,
                        dcm.Feature.SEX: "M",
                        dcm.Feature.DSA: False,
                        dcm.Feature.NIHSS: 7,
                        dcm.Feature.TIME: "24-48",
                        dcm.Feature.LETHALITY: True,
                        dcm.Feature.PATH: "dataset/train/study-002",
                        dcm.Feature.NUM_SUB: 0,
                        dcm.Feature.SUBFOLDERS: "",
                    },
                ]
            )
        )

    def test_get_study_returns_study_with_all_summary_fields(self):
        """Tests that get_study converts every row field into the correct study."""
        # Retrieve the study identified in setUp.
        study = self.catalog.get_study(self.study_id)

        # Check the type and values of the clinical fields and paths.
        self.assertIsInstance(study, dcm.Study)
        self.assertEqual(study.study_id, self.study_id)
        self.assertEqual(study.manufacturer, self.MANUFACTURER)
        self.assertEqual(study.model, self.MODEL)
        self.assertEqual(study.device, self.DEVICE)
        self.assertEqual(study.age, 85)
        self.assertEqual(study.sex, self.FEMALE)
        self.assertEqual(study.nihss, 4)
        self.assertEqual(study.time, self.TIME_RANGE)
        self.assertFalse(study.lethality)
        self.assertEqual(study.path, self.STUDY_PATH)
        self.assertEqual(study.num_subfolders, 2)
        self.assertEqual(study.subfolders, self.SUBFOLDERS)

    def test_get_statistics_returns_aggregated_catalog_statistics(self):
        """Tests that all computed catalog statistics are exposed in one dataclass."""
        statistics = self.catalog.get_statistics()

        self.assertIsInstance(statistics, dcm.StudyStatistics)
        self.assertEqual(statistics.lethality_percentage, 50.0)
        self.assertEqual(statistics.sex_distribution, {"F": 50.0, "M": 50.0})
        self.assertEqual(statistics.sex_missing_percentage, 0.0)
        self.assertEqual(statistics.age_mean, 78.5)
        self.assertEqual(statistics.age_std, 6.5)
        self.assertEqual(statistics.nihss_mean, 5.5)
        self.assertEqual(statistics.nihss_std, 1.5)
        self.assertEqual(statistics.nihss_missing_percentage, 0.0)
        self.assertEqual(statistics.time_distribution, {"0.0-24.0": 50.0, "24.0-48.0": 50.0})
        self.assertEqual(statistics.time_missing_percentage, 0.0)
        self.assertEqual(statistics.dsa_positive_percentage, 50.0)
        self.assertEqual(statistics.dsa_missing_percentage, 0.0)

    def test_get_subfolders_returns_normalized_folder_names(self):
        """Tests that subfolder names are returned as a tuple."""
        self.assertEqual(
            self.catalog.get_subfolders(self.study_id),
            self.SUBFOLDERS,
        )

    def test_studies_returns_all_studies_as_a_tuple(self):
        """Tests that the studies property exposes all studies as a tuple."""
        studies = self.catalog.studies

        # Check the collection type and identifier order.
        self.assertIsInstance(studies, tuple)
        self.assertEqual(
            tuple(study.study_id for study in studies),
            (self.STUDY_ID, self.SECOND_STUDY_ID),
        )

    def test_empty_subfolders_are_returned_as_empty_tuple(self):
        """Tests that the absence of subfolders produces an empty tuple."""
        self.assertEqual(self.catalog.get_subfolders(self.SECOND_STUDY_ID), ())

    def test_optional_columns_use_study_defaults_when_absent(self):
        """Tests that missing optional columns use the default values from Study."""
        # Keep fields required for catalog statistics while omitting optional Study metadata.
        catalog = dcm.StudyCatalog(
            pd.DataFrame(
                [
                    {
                        dcm.Feature.NAME: self.MINIMAL_STUDY_ID,
                        dcm.Feature.AGE: 50,
                        dcm.Feature.SEX: self.FEMALE,
                        dcm.Feature.DSA: False,
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.NIHSS: 5,
                        dcm.Feature.TIME: self.TIME_RANGE,
                    }
                ]
            )
        )

        # Retrieve the converted row to check its default values.
        study = catalog.get_study(self.MINIMAL_STUDY_ID)

        # Missing fields must be populated with the defaults defined by the model.
        self.assertEqual(study.study_id, self.MINIMAL_STUDY_ID)
        self.assertEqual(study.manufacturer, "")
        self.assertEqual(study.model, "")
        self.assertEqual(study.device, "")
        self.assertEqual(study.age, 50)
        self.assertEqual(study.sex, self.FEMALE)
        self.assertEqual(study.nihss, 5)
        self.assertEqual(study.time, self.TIME_RANGE)
        self.assertFalse(study.lethality)
        self.assertEqual(study.path, "")
        self.assertEqual(study.num_subfolders, 0)
        self.assertEqual(study.subfolders, ())

    def test_missing_required_feature_raises_feature_not_found_error(self):
        """Tests that missing statistics columns raise a feature-specific error."""
        required_features = (
            dcm.Feature.LETHALITY,
            dcm.Feature.SEX,
            dcm.Feature.AGE,
            dcm.Feature.DSA,
            dcm.Feature.NIHSS,
        )
        row = {
            dcm.Feature.NAME: self.MINIMAL_STUDY_ID,
            dcm.Feature.LETHALITY: False,
            dcm.Feature.SEX: self.FEMALE,
            dcm.Feature.AGE: 50,
            dcm.Feature.DSA: False,
            dcm.Feature.NIHSS: 5,
            dcm.Feature.TIME: self.TIME_RANGE,
        }

        for feature in required_features:
            with self.subTest(feature=feature):
                summary = pd.DataFrame([{key: value for key, value in row.items() if key != feature}])
                with self.assertRaisesRegex(ex.FeatureNotFoundError, feature.value):
                    dcm.StudyCatalog(summary)

    def test_sex_distribution_counts_missing_values(self):
        """Tests that missing sex values are counted separately from percentages."""
        catalog = dcm.StudyCatalog(
            pd.DataFrame(
                [
                    {
                        dcm.Feature.NAME: "female",
                        dcm.Feature.SEX: "F",
                        dcm.Feature.DSA: False,
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.AGE: 50,
                        dcm.Feature.NIHSS: 4,
                        dcm.Feature.TIME: self.TIME_RANGE,
                    },
                    {
                        dcm.Feature.NAME: "male",
                        dcm.Feature.SEX: "M",
                        dcm.Feature.DSA: False,
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.AGE: 60,
                        dcm.Feature.NIHSS: 6,
                        dcm.Feature.TIME: self.TIME_RANGE,
                    },
                    {
                        dcm.Feature.NAME: "missing",
                        dcm.Feature.SEX: pd.NA,
                        dcm.Feature.DSA: False,
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.AGE: 70,
                        dcm.Feature.NIHSS: 8,
                        dcm.Feature.TIME: self.TIME_RANGE,
                    },
                ]
            )
        )

        self.assertEqual(catalog.get_sex_distribution(), {"F": 33.33, "M": 33.33})
        self.assertEqual(np.around(catalog.get_sex_missing_count(), 2), 33.33)

    def test_time_and_dsa_distributions_include_missing_percentages(self):
        """Tests time-range grouping and DSA missing-value percentages."""
        catalog = dcm.StudyCatalog(
            pd.DataFrame(
                [
                    {
                        dcm.Feature.NAME: "range-single",
                        dcm.Feature.AGE: 50,
                        dcm.Feature.SEX: "F",
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.TIME: "2.5",
                        dcm.Feature.DSA: True,
                        dcm.Feature.NIHSS: 4,
                    },
                    {
                        dcm.Feature.NAME: "range-pair",
                        dcm.Feature.AGE: 60,
                        dcm.Feature.SEX: "M",
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.TIME: "2.5-2.5",
                        dcm.Feature.DSA: False,
                        dcm.Feature.NIHSS: 8,
                    },
                    {
                        dcm.Feature.NAME: "missing",
                        dcm.Feature.AGE: 70,
                        dcm.Feature.SEX: "F",
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.TIME: "7-8",
                        dcm.Feature.DSA: pd.NA,
                        dcm.Feature.NIHSS: pd.NA,
                    },
                ]
            )
        )

        self.assertEqual(catalog.get_time_distribution(), {"2.5-2.5": 66.67, "7.0-8.0": 33.33})
        self.assertEqual(catalog.get_time_missing_percentage(), 0.0)
        self.assertEqual(catalog.get_dsa_percentage(), 33.33)
        self.assertEqual(catalog.get_dsa_missing_percentage(), 33.33)
        self.assertEqual(catalog.get_nihss_distribution(), (6.0, 2.0, 33.33))

    def test_unknown_study_raises_study_not_found_error(self):
        """Tests that looking up an unknown identifier raises the expected error."""
        with self.assertRaisesRegex(ex.StudyNotFoundError, self.MISSING_STUDY_ID):
            self.catalog.get_study(self.MISSING_STUDY_ID)
