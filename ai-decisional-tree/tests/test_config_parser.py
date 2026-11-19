import unittest
from unittest.mock import Mock

import src.common as src
import src.config_parser as cp
import src.config_parser.data_structures as ds
import src.config_parser.exceptions as ex


class ConfigParserTests(unittest.TestCase):
    """Tests typed configuration access and translation of parser errors."""

    QUOTED_DATASET_NAME: str = '"owner/dataset"'
    OUTPUT_PATH: str = "extracted"
    COUNT_OPTION: str = "count"
    RATIO_OPTION: str = "ratio"
    MISSING_SECTION: str = "Not present"
    MISSING_OPTION: str = "not present"

    def setUp(self):
        self.folder_manager: Mock = Mock(spec_set=src.FolderManager)
        self.folder_manager.config_file_path = "missing-config.ini"
        self.parser = cp.ConfigParser(self.folder_manager)
        self.parser.config.read_dict(
            {
                "Dataset": {
                    "name": self.QUOTED_DATASET_NAME,
                    "output_path": self.OUTPUT_PATH,
                    self.COUNT_OPTION: "12",
                    self.RATIO_OPTION: "2.75",
                },
                "Storing data": {
                    "save img": "yes",
                    "save video": "no",
                    "save img filtered": "true",
                    "save video filtered": "false",
                },
            }
        )

    def test_dataset_properties_read_and_clean_string_values(self):
        """Check that dataset properties return normalized values from configuration."""
        self.assertEqual(self.parser.dataset_name, self.QUOTED_DATASET_NAME.replace('"', ""))
        self.assertEqual(self.parser.dataset_output_path, self.OUTPUT_PATH)

    def test_typed_accessors_convert_values(self):
        """Verify integer, float, and boolean accessors convert configured strings."""
        self.assertEqual(self.parser.get_int(ds.Section.DATASET, self.COUNT_OPTION), 12)
        self.assertEqual(self.parser.get_float(ds.Section.DATASET, self.RATIO_OPTION), 2.75)
        self.assertTrue(self.parser.get_boolean(ds.Section.STORAGE, ds.Option.SAVE_IMG))

    def test_string_accessor_can_preserve_quotes(self):
        """Confirm callers can opt out of removing quotes from string values."""
        self.assertEqual(self.parser.get(ds.Section.DATASET, ds.Option.NAME, to_remove=False), self.QUOTED_DATASET_NAME)

    def test_all_storage_properties_are_read_as_booleans(self):
        """Check all storage properties expose their configured boolean values."""
        self.assertTrue(self.parser.save_img)
        self.assertFalse(self.parser.save_video)
        self.assertTrue(self.parser.save_img_flt)
        self.assertFalse(self.parser.save_video_flt)

    def test_missing_section_is_translated(self):
        """Ensure an absent configuration section becomes the public domain error."""
        with self.assertRaisesRegex(ex.NoSectionError, self.MISSING_SECTION):
            self.parser.get(self.MISSING_SECTION, ds.Option.NAME)

    def test_missing_option_is_translated(self):
        """Ensure an absent option becomes the public domain error."""
        with self.assertRaisesRegex(ex.NoOptionError, self.MISSING_OPTION):
            self.parser.get(ds.Section.DATASET, self.MISSING_OPTION)

    def test_invalid_typed_value_is_translated(self):
        """Ensure an invalid numeric value is reported as a configuration error."""
        self.parser.config.set(ds.Section.DATASET, self.COUNT_OPTION, "twelve")
        with self.assertRaisesRegex(ex.ConfigError, "invalid literal"):
            self.parser.get_int(ds.Section.DATASET, self.COUNT_OPTION)

    def test_invalid_boolean_is_translated(self):
        """Ensure an unrecognized boolean value is reported as a configuration error."""
        self.parser.config.set(ds.Section.STORAGE, ds.Option.SAVE_IMG, "sometimes")
        with self.assertRaises(ex.ConfigError):
            _ = self.parser.save_img
