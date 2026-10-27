import unittest

import pandas as pd

import src.data.common as dcm
import src.data.common.exceptions as ex


class StudyCatalogTests(unittest.TestCase):
    def setUp(self):
        self.study_id = "study-001"
        self.catalog = dcm.StudyCatalog(
            pd.DataFrame(
                [
                    {
                        dcm.Feature.NAME: self.study_id,
                        dcm.Feature.MANUFACTURER: "SIEMENS",
                        dcm.Feature.MODEL: "Emotion 16",
                        dcm.Feature.DEVICE: "SIEMENS Emotion 16",
                        dcm.Feature.AGE: 85,
                        dcm.Feature.SEX: "F",
                        dcm.Feature.NIHSS: 4,
                        dcm.Feature.TIME: "0-24",
                        dcm.Feature.LETHALITY: False,
                        dcm.Feature.PATH: "dataset/train/study-001",
                        dcm.Feature.NUM_SUB: 2,
                        dcm.Feature.SUBFOLDERS: "00000, 00001",
                    },
                    {
                        dcm.Feature.NAME: "study-002",
                        dcm.Feature.MANUFACTURER: "GE",
                        dcm.Feature.MODEL: "Revolution",
                        dcm.Feature.DEVICE: "GE Revolution",
                        dcm.Feature.AGE: 72,
                        dcm.Feature.SEX: "M",
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
        study = self.catalog.get_study(self.study_id)

        self.assertIsInstance(study, dcm.Study)
        self.assertEqual(study.study_id, self.study_id)
        self.assertEqual(study.manufacturer, "SIEMENS")
        self.assertEqual(study.model, "Emotion 16")
        self.assertEqual(study.device, "SIEMENS Emotion 16")
        self.assertEqual(study.age, 85)
        self.assertEqual(study.sex, "F")
        self.assertEqual(study.nihss, 4)
        self.assertEqual(study.time, "0-24")
        self.assertFalse(study.lethality)
        self.assertEqual(study.path, "dataset/train/study-001")
        self.assertEqual(study.num_subfolders, 2)
        self.assertEqual(study.subfolders, ("00000", "00001"))

    def test_get_subfolders_returns_normalized_folder_names(self):
        self.assertEqual(
            self.catalog.get_subfolders(self.study_id),
            ("00000", "00001"),
        )

    def test_studies_returns_all_studies_as_a_tuple(self):
        studies = self.catalog.studies

        self.assertIsInstance(studies, tuple)
        self.assertEqual(
            tuple(study.study_id for study in studies),
            ("study-001", "study-002"),
        )

    def test_empty_subfolders_are_returned_as_empty_tuple(self):
        self.assertEqual(self.catalog.get_subfolders("study-002"), ())

    def test_optional_columns_use_study_defaults_when_absent(self):
        catalog = dcm.StudyCatalog(
            pd.DataFrame([{dcm.Feature.NAME: "minimal-study"}])
        )

        study = catalog.get_study("minimal-study")

        self.assertEqual(study.study_id, "minimal-study")
        self.assertEqual(study.manufacturer, "")
        self.assertEqual(study.model, "")
        self.assertEqual(study.device, "")
        self.assertEqual(study.age, -1)
        self.assertEqual(study.sex, "")
        self.assertEqual(study.nihss, -1)
        self.assertEqual(study.time, "")
        self.assertEqual(study.lethality, "")
        self.assertEqual(study.path, "")
        self.assertEqual(study.num_subfolders, 0)
        self.assertEqual(study.subfolders, ())

    def test_unknown_study_raises_study_not_found_error(self):
        with self.assertRaisesRegex(ex.StudyNotFoundError, "missing-study"):
            self.catalog.get_study("missing-study")
