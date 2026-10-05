import os
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, call, patch
from zipfile import ZipFile
from requests.exceptions import HTTPError, SSLError

from tests.helper import OsMockFolder as omf

from src.common.folder_manager import FolderManager
from src.common.folder_manager.data_structures import FileName, FolderName
from src.common.os_manager import OsManager, OsWrapper


class OsWrapperTests(unittest.TestCase):
    DATASET_NAME: str = "owner/dataset"
    OUTPUT_DIR: str = "extracted"

    def setUp(self) -> None:
        self.os_wrapper: OsWrapper = OsWrapper()

    def test_dataset_download_without_ssl_fallback(self):
        with patch(omf.OS_DATASET_DOWNLOAD, return_value=self.OUTPUT_DIR) as download:
            with patch(omf.OS_TRUSTSTORE) as inject:
                self.assertEqual(self.os_wrapper.download_dataset(self.DATASET_NAME, self.OUTPUT_DIR), self.OUTPUT_DIR)
                download.assert_called_once_with(self.DATASET_NAME, output_dir=self.OUTPUT_DIR)
                inject.assert_not_called()

    def test_certificate_failure_retries_with_system_certificates(self):
        events = []

        def download_dataset(*args, **kwargs):
            events.append("download")
            if len(events) == 1:
                raise SSLError("[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate")
            return self.OUTPUT_DIR

        with patch(omf.OS_DATASET_DOWNLOAD, side_effect=download_dataset) as download:
            with patch(omf.OS_TRUSTSTORE, side_effect=lambda: events.append("truststore")) as inject:
                self.assertEqual(self.os_wrapper.download_dataset(self.DATASET_NAME, self.OUTPUT_DIR), self.OUTPUT_DIR)
                self.assertEqual(events, ["download", "truststore", "download"])
                self.assertEqual(download.call_args_list, [
                    call(self.DATASET_NAME, output_dir=self.OUTPUT_DIR),
                    call(self.DATASET_NAME, output_dir=self.OUTPUT_DIR),
                ])
                inject.assert_called_once_with()

    def test_certificate_failure_after_retry_propagates(self):
        with patch(omf.OS_DATASET_DOWNLOAD, side_effect=SSLError("CERTIFICATE_VERIFY_FAILED")) as download:
            with patch(omf.OS_TRUSTSTORE) as inject:
                with self.assertRaises(SSLError):
                    self.os_wrapper.download_dataset(self.DATASET_NAME, self.OUTPUT_DIR)
                self.assertEqual(download.call_count, 2)
                inject.assert_called_once_with()

    def test_other_download_failures_do_not_enable_truststore(self):
        for error in (SSLError("TLS handshake failed"), HTTPError("401 Unauthorized"), OSError("disk full")):
            with self.subTest(error=error):
                with patch(omf.OS_DATASET_DOWNLOAD, side_effect=error) as download:
                    with patch(omf.OS_TRUSTSTORE) as inject:
                        with self.assertRaises(type(error)):
                            self.os_wrapper.download_dataset(self.DATASET_NAME, self.OUTPUT_DIR)
                        download.assert_called_once_with(self.DATASET_NAME, output_dir=self.OUTPUT_DIR)
                        inject.assert_not_called()

    def test_interface_is_abstract(self):
        with self.assertRaises(TypeError):
            OsManager()

    def test_os_path_operations(self):
        wrapper: OsWrapper = OsWrapper()
        path: str = os.path.join("config", "config.ini")
        self.assertEqual(wrapper.abspath(path), os.path.abspath(path))
        self.assertEqual(wrapper.dirname(path), os.path.dirname(path))

    def test_path_operations_delegate(self):
        wrapper: OsWrapper = OsWrapper()
        for path in ("config", Path("config")):
            for method in ("exists", "is_file", "is_dir", "iterdir", "unlink", "rmdir"):
                with self.subTest(path=path, method=method):
                    with patch(omf.OS_PATH) as path_class:
                        path_mock = path_class.return_value
                        result = getattr(wrapper, method)(path)
                        path_class.assert_called_once_with(path)
                        getattr(path_mock, method).assert_called_once_with()
                        if method in ("exists", "is_file", "is_dir", "iterdir"):
                            self.assertIs(result, getattr(path_mock, method).return_value)
                        else:
                            self.assertIsNone(result)

    def test_mkdir_delegates_options(self):
        with patch(omf.OS_PATH) as path_class:
            self.os_wrapper.mkdir("config", parents=True, exist_ok=True)
            path_class.assert_called_once_with("config")
            path_class.return_value.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_filesystem_errors_propagate(self):
        with patch(omf.OS_PATH) as path_class:
            path_class.return_value.unlink.side_effect = PermissionError("denied")
            with self.assertRaises(PermissionError):
                self.os_wrapper.unlink("config.ini")

    def test_zip_integrity(self):
        buffer = BytesIO()
        with ZipFile(buffer, "w") as archive:
            archive.writestr("dataset.csv", b"dataset-content")
        valid_zip = buffer.getvalue()
        cases = [
            (valid_zip, True),
            (b"not a zip", False),
            (valid_zip[:20], False),
            (valid_zip.replace(b"dataset-content", b"damaged-content"), False),
        ]
        for content, expected in cases:
            with self.subTest(content=content):
                with patch(
                    omf.OS_ZIPFILE,
                    side_effect=lambda path: ZipFile(BytesIO(content)),
                ):
                    self.assertEqual(self.os_wrapper.is_valid_zip("dataset.zip"), expected)

    def test_zip_permission_errors_propagate(self):
        with patch(
            omf.OS_ZIPFILE,
            side_effect=PermissionError("denied"),
        ):
            with self.assertRaises(PermissionError):
                self.os_wrapper.is_valid_zip("dataset.zip")


class FolderManagerTests(unittest.TestCase):
    def setUp(self):
        self.os_manager: Mock = Mock(spec_set=OsManager)
        self.base_path = Path("application")
        self.manager = FolderManager(str(self.base_path), self.os_manager)

    def test_default_wrapper_preserves_existing_constructor(self):
        with patch(omf.OS_WRAPPER) as wrapper:
            manager: FolderManager = FolderManager("application")
            manager.folder_exists(FolderName.CONFIG)
            wrapper.return_value.exists.assert_called_once_with(Path("application") / "config")

    def test_file_exists_uses_injected_manager(self):
        path: Path = self.base_path / FolderName.CONFIG / FileName.CONFIG
        self.os_manager.exists.return_value = True
        self.os_manager.is_file.return_value = True
        self.assertTrue(self.manager.file_exists(FolderName.CONFIG, FileName.CONFIG))
        self.os_manager.exists.assert_called_once_with(path)
        self.os_manager.is_file.assert_called_once_with(path)

    def test_missing_file_short_circuits(self):
        self.os_manager.exists.return_value = False
        self.assertFalse(self.manager.file_exists(FolderName.CONFIG, FileName.CONFIG))
        self.os_manager.is_file.assert_not_called()

    def test_folder_exists_uses_injected_manager(self):
        self.os_manager.exists.return_value = True
        self.os_manager.is_dir.return_value = True
        self.assertTrue(self.manager.folder_exists(FolderName.CONFIG))
        self.os_manager.is_dir.assert_called_once_with(self.base_path / FolderName.CONFIG)

    def test_create_folder_uses_injected_manager(self):
        self.manager.create_folder(FolderName.CONFIG)
        self.os_manager.mkdir.assert_called_once_with(
            self.base_path / FolderName.CONFIG, parents=True, exist_ok=True,
        )

    def test_delete_nested_folder_uses_full_paths(self):
        folder: Path = self.base_path / FolderName.CONFIG
        nested: Path = folder / "nested"
        file_path: Path = nested / "config.ini"
        self.os_manager.exists.return_value = True
        self.os_manager.is_dir.return_value = True
        self.os_manager.iterdir.side_effect = lambda path: iter({
            folder: [nested],
            nested: [file_path],
        }[path])
        self.os_manager.is_file.side_effect = lambda path: path == file_path

        self.manager.delete_folder(FolderName.CONFIG)

        self.os_manager.unlink.assert_called_once_with(file_path)
        self.assertEqual(self.os_manager.iterdir.call_args_list, [call(folder), call(nested)])
        self.assertEqual(self.os_manager.rmdir.call_args_list, [call(nested), call(folder)])

    def test_delete_missing_folder_does_not_modify_filesystem(self):
        self.os_manager.exists.return_value = False
        self.manager.delete_folder(FolderName.CONFIG)
        self.os_manager.iterdir.assert_not_called()
        self.os_manager.unlink.assert_not_called()
        self.os_manager.rmdir.assert_not_called()
