import unittest
from unittest.mock import Mock, call

import src.common as src
import src.config_parser as cp
import src.data.data_loader as dl
import src.data.data_loader.exceptions as ex
from requests.exceptions import SSLError


class DataLoaderTests(unittest.TestCase):
    """Tests the data loader's configuration, downloads, and error handling."""

    # Minimal configuration for creating a DataLoader without reading real files.
    CONFIG_MOCK = {
        "Dataset": {
            "name": "owner/dataset",
            "output_path": "extracted",
        }
    }

    def setUp(self):
        """Sets up mocked dependencies and a DataLoader isolated from the filesystem."""
        # The mock exposes only the OsManager interface and intercepts OS calls.
        self.os_manager: Mock = Mock(spec_set=src.OsManager)
        self.base_path: str = "./"
        # Make filesystem checks return true by default.
        self.os_manager.exists.return_value = True
        self.os_manager.is_dir.return_value = True
        self.os_manager.is_file.return_value = True
        # Connect the folder manager to the mock so all operations remain simulated.
        self.folder_manager: src.FolderManager = src.FolderManager(self.base_path, self.os_manager)
        # Load the test configuration directly into memory.
        self.config_parser: cp.ConfigParser = cp.ConfigParser(self.folder_manager)
        self.config_parser.config.read_dict(self.CONFIG_MOCK)
        # Mock the CSV manager, although these tests do not read CSV files.
        self.csv_manager: Mock = Mock(spec_set=src.CsvManager)
        # Calculate the expected path for the extracted dataset folder.
        self.dataset_path: str = self.folder_manager.get_folder_path(folder_name="extracted", str_format=True)
        # Create the system under test with all dependencies mocked.
        self.loader: dl.DataLoader = dl.DataLoader(
            folder_manager=self.folder_manager,
            config_parser=self.config_parser,
            csv_manager=self.csv_manager,
            os_manager=self.os_manager,
        )
        # Exclude setup calls from the call count.
        self.os_manager.reset_mock()

    def test_configuration_is_read_in_memory(self):
        """Tests that configuration values are available without filesystem access."""
        # The values read must match the mock configuration.
        self.assertEqual(self.config_parser.dataset_name, "owner/dataset")
        self.assertEqual(self.config_parser.dataset_output_path, "extracted")
        # Reading the configuration alone must not check files or folders.
        self.os_manager.exists.assert_not_called()
        self.os_manager.is_file.assert_not_called()

    def test_download_uses_configured_directory_and_returns_resolved_path(self):
        """Tests that a missing dataset is downloaded to the configured folder."""
        # Simulate a missing folder and the path returned by the download.
        self.os_manager.exists.return_value = False
        self.os_manager.download_dataset.return_value = self.dataset_path
        # The loader must return the downloaded dataset path.
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        # Check the dataset name and destination passed to the download method.
        self.os_manager.download_dataset.assert_called_once_with("owner/dataset", self.dataset_path)

    def test_existing_dataset_skips_download_and_returns_resolved_path(self):
        """Tests that an existing dataset is not downloaded again."""
        # When the folder exists, the loader immediately returns its path.
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        # No download request should be made.
        self.os_manager.download_dataset.assert_not_called()

    def test_absolute_extract_path_is_preserved(self):
        """Tests that the specified extraction path is used unchanged."""
        # Set the explicit path and simulate the dataset being absent there.
        extract_path: str = "extracted"
        self.config_parser.config.set("Dataset", "extract_path", extract_path)
        self.os_manager.exists.return_value = False
        # Create the loader after updating the configuration.
        loader = dl.DataLoader(self.folder_manager, self.config_parser, os_manager=self.os_manager)
        loader.load_data()
        # Check that the configured path is passed directly to the download method.
        self.os_manager.download_dataset.assert_called_once_with("owner/dataset", extract_path)

    def test_repeated_loads_delegate_cache_management(self):
        """Tests that repeated loads delegate cache reuse to the downloader each time."""
        # Simulate a missing local dataset and a successful download for both calls.
        self.os_manager.exists.return_value = False
        self.os_manager.download_dataset.return_value = self.dataset_path
        # Load twice and check the path returned by each call.
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        # Both calls must pass the same arguments to the downloader.
        self.assertEqual(
            self.os_manager.download_dataset.call_args_list,
            [
                call("owner/dataset", self.dataset_path),
                call("owner/dataset", self.dataset_path),
            ],
        )

    def test_download_failure_propagates(self):
        """Tests that repeated failures raise DatasetLoadError after four attempts."""
        # Force the download path and simulate an SSL error on every attempt.
        self.os_manager.exists.return_value = False
        self.os_manager.download_dataset.side_effect = SSLError("certificate verification failed")
        # After the configured attempts, the loader must raise its domain-specific error.
        with self.assertRaises(ex.DatasetLoadError):
            self.loader.load_data()
        # Confirm that exactly four attempts were made.
        self.assertEqual(self.os_manager.download_dataset.call_count, 4)
