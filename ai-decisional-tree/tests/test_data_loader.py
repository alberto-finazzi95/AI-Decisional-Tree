import unittest
from unittest.mock import Mock, call

from requests.exceptions import SSLError

import src.common as cm
import src.config_parser as cp
import src.data.data_loader as dl
import src.data.data_loader.exceptions as ex


class DataLoaderTests(unittest.TestCase):
    CONFIG_MOCK = {
        "Dataset": {
            "name": "owner/dataset",
            "output_path": "extracted",
        }
    }

    def setUp(self):
        # Setting the os manager
        self.os_manager: Mock = Mock(spec_set=cm.OsManager)
        self.base_path: str = "./"
        # All files and folders exist by default
        self.os_manager.exists.return_value = True
        self.os_manager.is_dir.return_value = True
        self.os_manager.is_file.return_value = True
        # Setting the folder manager and config parser
        self.folder_manager: cm.FolderManager = cm.FolderManager(self.base_path, self.os_manager)
        # Setting the config parser
        self.config_parser: cp.ConfigParser = cp.ConfigParser(self.folder_manager)
        self.config_parser.config.read_dict(self.CONFIG_MOCK)
        # Setting the csv manager
        self.csv_manager: Mock = Mock(spec_set=cm.CsvManager)
        # Setting the dataset path
        self.dataset_path: str = self.folder_manager.get_folder_path(folder_name="extracted", str_format=True)
        # Setting the data loader
        self.loader: dl.DataLoader = dl.DataLoader(
            folder_manager=self.folder_manager,
            config_parser=self.config_parser,
            csv_manager=self.csv_manager,
            os_manager=self.os_manager
        )
        self.os_manager.reset_mock()

    def test_configuration_is_read_in_memory(self):
        self.assertEqual(self.config_parser.dataset_name, "owner/dataset")
        self.assertEqual(self.config_parser.dataset_output_path, "extracted")
        self.os_manager.exists.assert_not_called()
        self.os_manager.is_file.assert_not_called()

    def test_download_uses_configured_directory_and_returns_resolved_path(self):
        self.os_manager.exists.return_value = False
        self.os_manager.download_dataset.return_value = self.dataset_path
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        self.os_manager.download_dataset.assert_called_once_with("owner/dataset", self.dataset_path)

    def test_existing_dataset_skips_download_and_returns_resolved_path(self):
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        self.os_manager.download_dataset.assert_not_called()

    def test_absolute_extract_path_is_preserved(self):
        extract_path: str = "extracted"
        self.config_parser.config.set("Dataset", "extract_path", extract_path)
        self.os_manager.exists.return_value = False
        loader = dl.DataLoader(self.folder_manager, self.config_parser, os_manager=self.os_manager)
        loader.load_data()
        self.os_manager.download_dataset.assert_called_once_with("owner/dataset", extract_path)

    def test_repeated_loads_delegate_cache_management(self):
        self.os_manager.exists.return_value = False
        self.os_manager.download_dataset.return_value = self.dataset_path
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        self.assertEqual(
            self.os_manager.download_dataset.call_args_list,
            [
                call("owner/dataset", self.dataset_path),
                call("owner/dataset", self.dataset_path),
            ],
        )

    def test_download_failure_propagates(self):
        self.os_manager.exists.return_value = False
        self.os_manager.download_dataset.side_effect = SSLError("certificate verification failed")
        with self.assertRaises(ex.DatasetLoadError):
            self.loader.load_data()
        self.assertEqual(self.os_manager.download_dataset.call_count, 4)
