import unittest
from unittest.mock import Mock, call

from requests.exceptions import SSLError

from src.common import FolderManager, OsManager
from src.config_parser import ConfigParser
from src.data_loader import DataLoader


class DataLoaderTests(unittest.TestCase):
    CONFIG_MOCK = {
        "Dataset": {
            "name": "owner/dataset",
            "output_path": "extracted",
        }
    }

    def setUp(self):
        self.os_manager: Mock = Mock(spec_set=OsManager)
        self.base_path: str = "./"
        self.os_manager.exists.return_value = True
        self.os_manager.is_file.return_value = True
        self.folder_manager = FolderManager(self.base_path, self.os_manager)
        self.config_parser = ConfigParser(self.folder_manager)
        self.config_parser.config.read_dict(self.CONFIG_MOCK)
        self.dataset_path: str = self.folder_manager.get_folder_path(folder_name="extracted", str_format=True)
        self.loader: DataLoader = DataLoader(self.folder_manager, self.config_parser, self.os_manager)
        self.os_manager.reset_mock()

    def test_configuration_is_read_in_memory(self):
        self.assertEqual(self.config_parser.dataset_name, "owner/dataset")
        self.assertEqual(self.config_parser.dataset_output_path, "extracted")
        self.os_manager.exists.assert_not_called()
        self.os_manager.is_file.assert_not_called()

    def test_download_uses_configured_directory_and_returns_resolved_path(self):
        self.os_manager.download_dataset.return_value = self.dataset_path
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        self.os_manager.download_dataset.assert_called_once_with("owner/dataset", self.dataset_path)

    def test_absolute_extract_path_is_preserved(self):
        extract_path: str = "extracted"
        self.config_parser.config.set("Dataset", "extract_path", extract_path)
        loader = DataLoader(self.folder_manager, self.config_parser, self.os_manager)
        loader.load_data()
        self.os_manager.download_dataset.assert_called_once_with("owner/dataset", extract_path)

    def test_repeated_loads_delegate_cache_management(self):
        self.os_manager.download_dataset.return_value = self.dataset_path
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        self.assertEqual(self.os_manager.download_dataset.call_args_list, [
            call("owner/dataset", self.dataset_path),
            call("owner/dataset", self.dataset_path),
        ])

    def test_download_failure_propagates(self):
        self.os_manager.download_dataset.side_effect = SSLError("certificate verification failed")
        with self.assertRaises(SSLError):
            self.loader.load_data()
        self.os_manager.download_dataset.assert_called_once_with("owner/dataset", self.dataset_path)
