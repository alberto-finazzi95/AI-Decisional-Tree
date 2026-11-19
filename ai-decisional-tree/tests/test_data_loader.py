import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

import pandas as pd
import src.common as src
import src.config_parser as cp
import src.data.common as dcm
import src.data.data_loader as dl
import src.data.data_loader.exceptions as ex
from requests.exceptions import SSLError


class DataLoaderTests(unittest.TestCase):
    """Tests the data loader's configuration, downloads, and error handling."""

    DATASET_SECTION: str = "Dataset"
    DATASET_NAME: str = "owner/dataset"
    OUTPUT_PATH: str = "extracted"
    TRAIN_STUDY: str = "train-study"
    VALIDATION_STUDY: str = "validation-study"
    TEST_STUDY: str = "test-study"
    MISSING_STUDY: str = "missing-study"
    OUTPUT_STUDY: str = "study-1"
    SUMMARY_READ_CSV: str = "src.data.data_loader.data_loader.pd.read_csv"
    SUBFOLDERS_METHOD: str = "get_subfolders"
    SORTED_FRAME_FOLDERS: tuple[str, ...] = ("00000", "00001", "00002")

    # Minimal configuration for creating a DataLoader without reading real files.
    CONFIG_MOCK = {
        DATASET_SECTION: {
            "name": DATASET_NAME,
            "output_path": OUTPUT_PATH,
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
        self.dataset_path: str = self.folder_manager.get_folder_path(folder_name=self.OUTPUT_PATH, str_format=True)
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
        self.assertEqual(self.config_parser.dataset_name, self.DATASET_NAME)
        self.assertEqual(self.config_parser.dataset_output_path, self.OUTPUT_PATH)
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
        self.os_manager.download_dataset.assert_called_once_with(self.DATASET_NAME, self.dataset_path)

    def test_existing_dataset_skips_download_and_returns_resolved_path(self):
        """Tests that an existing dataset is not downloaded again."""
        # When the folder exists, the loader immediately returns its path.
        self.assertEqual(self.loader.load_data(), self.dataset_path)
        # No download request should be made.
        self.os_manager.download_dataset.assert_not_called()

    def test_absolute_extract_path_is_preserved(self):
        """Tests that the specified extraction path is used unchanged."""
        # Set the explicit path and simulate the dataset being absent there.
        extract_path: str = self.OUTPUT_PATH
        self.config_parser.config.set(self.DATASET_SECTION, "extract_path", extract_path)
        self.os_manager.exists.return_value = False
        # Create the loader after updating the configuration.
        loader = dl.DataLoader(self.folder_manager, self.config_parser, os_manager=self.os_manager)
        loader.load_data()
        # Check that the configured path is passed directly to the download method.
        self.os_manager.download_dataset.assert_called_once_with(self.DATASET_NAME, extract_path)

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
                call(self.DATASET_NAME, self.dataset_path),
                call(self.DATASET_NAME, self.dataset_path),
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

    def test_download_retries_then_returns_successful_path(self):
        """Tests that a transient download failure is retried and later succeeds."""
        self.os_manager.exists.return_value = False
        self.os_manager.download_dataset.side_effect = [
            SSLError("temporary certificate failure"),
            self.dataset_path,
        ]

        self.assertEqual(self.loader.load_data(), self.dataset_path)

        self.assertEqual(self.os_manager.download_dataset.call_count, 2)

    def test_process_data_partitions_summaries_and_builds_catalogs(self):
        """Tests split selection, file metadata enrichment, and catalog construction."""
        summary = pd.DataFrame(
            [
                {dcm.Feature.NAME: self.TRAIN_STUDY, dcm.Feature.PART: dcm.DatasetType.TRAIN},
                {dcm.Feature.NAME: self.VALIDATION_STUDY, dcm.Feature.PART: dcm.DatasetType.VALIDATION},
                {dcm.Feature.NAME: self.TEST_STUDY, dcm.Feature.PART: dcm.DatasetType.TEST},
            ]
        )
        with patch(self.SUMMARY_READ_CSV, return_value=summary) as read_csv:
            with patch.object(
                self.folder_manager,
                self.SUBFOLDERS_METHOD,
                return_value=[
                    self.SORTED_FRAME_FOLDERS[2],
                    "notes",
                    self.SORTED_FRAME_FOLDERS[0],
                    self.SORTED_FRAME_FOLDERS[1],
                ],
            ) as get_subfolders:
                self.loader.process_data()

        read_csv.assert_called_once_with(self.loader._summary_csv_path)
        self.assertEqual(get_subfolders.call_count, 3)
        train_study = self.loader.get_study_catalog(dcm.DatasetType.TRAIN).get_study(self.TRAIN_STUDY)
        self.assertEqual(
            train_study.path,
            self.loader._get_data_path(
                self.TRAIN_STUDY,
                self.loader._get_dataset_type_folder(dcm.DatasetType.TRAIN),
            ),
        )
        self.assertEqual(train_study.num_subfolders, 3)
        self.assertEqual(train_study.subfolders, self.SORTED_FRAME_FOLDERS)
        self.assertEqual(
            self.loader.get_study_catalog(dcm.DatasetType.VALIDATION).get_study(self.VALIDATION_STUDY).num_subfolders,
            3,
        )
        self.assertEqual(
            self.loader.get_study_catalog(dcm.DatasetType.TEST).get_study(self.TEST_STUDY).subfolders,
            self.SORTED_FRAME_FOLDERS,
        )

    def test_process_data_raises_for_missing_study_directory(self):
        """Tests that missing study paths are reported with the affected split."""
        summary = pd.DataFrame([{dcm.Feature.NAME: self.MISSING_STUDY, dcm.Feature.PART: dcm.DatasetType.TRAIN}])
        missing_path = self.loader._get_data_path(
            self.MISSING_STUDY,
            self.loader._get_dataset_type_folder(dcm.DatasetType.TRAIN),
        )
        self.os_manager.exists.side_effect = lambda path: path != missing_path

        with patch(self.SUMMARY_READ_CSV, return_value=summary):
            with patch.object(self.folder_manager, self.SUBFOLDERS_METHOD) as get_subfolders:
                with self.assertRaisesRegex(ex.MissingFilesError, self.MISSING_STUDY):
                    self.loader.process_data()
        get_subfolders.assert_not_called()

    def test_unknown_dataset_split_raises_catalog_not_found(self):
        """Tests that catalog lookup reports a split that was never configured."""
        self.loader._study_catalogs = {}
        with self.assertRaises(ex.StudyCatalogNotFound):
            self.loader.get_study_catalog(dcm.DatasetType.TRAIN)

    def test_store_volume_creates_output_directory_and_writes_compressed_parquet(self):
        """Tests the output location and Parquet options for persisted volume data."""
        frame = pd.DataFrame({"value": [1, 2]})
        self.os_manager.exists.return_value = False
        with patch.object(pd.DataFrame, "to_parquet") as to_parquet:
            self.loader.store_volume(frame, self.OUTPUT_STUDY, dcm.DatasetType.TRAIN)

        volumes_folder = self.loader.get_volumes_folder(dcm.DatasetType.TRAIN)
        self.os_manager.mkdir.assert_called_once_with(Path(volumes_folder), parents=True, exist_ok=True)
        to_parquet.assert_called_once_with(
            self.loader._get_patient_volume_path(self.OUTPUT_STUDY, volumes_folder),
            compression="snappy",
            index=False,
        )
