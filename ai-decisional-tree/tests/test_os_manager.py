import os
import unittest
from pathlib import Path
from unittest.mock import call, patch

from requests.exceptions import HTTPError, SSLError

import src as src
from tests.helper import OsMockFolder as omf


class OsWrapperTests(unittest.TestCase):
    """Tests the system operations and downloads handled by OsWrapper."""

    DATASET_NAME: str = "owner/dataset"
    OUTPUT_DIR: str = "extracted"

    def setUp(self) -> None:
        """Creates the concrete wrapper implementation under test."""
        self.os_wrapper: src.OsWrapper = src.OsWrapper()

    def test_dataset_download_without_ssl_fallback(self):
        """Tests that a successful download does not enable the SSL fallback."""
        # Simulate a successful download and intercept trust store activation.
        with patch(omf.OS_DATASET_DOWNLOAD, return_value=self.OUTPUT_DIR) as download:
            with patch(omf.OS_TRUSTSTORE) as inject:
                # The returned path and arguments must match the request.
                self.assertEqual(self.os_wrapper.download_dataset(self.DATASET_NAME, self.OUTPUT_DIR), self.OUTPUT_DIR)
                download.assert_called_once_with(self.DATASET_NAME, output_dir=self.OUTPUT_DIR)
                # The fallback is unnecessary when the first download succeeds.
                inject.assert_not_called()

    def test_certificate_failure_retries_with_system_certificates(self):
        """Tests that a certificate error enables the trust store and retries the download."""
        # Record simulated events to verify the retry sequence.
        events = []

        def download_dataset(*args, **kwargs):
            """Fails on the first download and returns the folder on the second."""
            events.append("download")
            if len(events) == 1:
                raise SSLError("[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate")
            return self.OUTPUT_DIR

        # Replace the download and trust store with test-controlled functions.
        with patch(omf.OS_DATASET_DOWNLOAD, side_effect=download_dataset) as download:
            with patch(omf.OS_TRUSTSTORE, side_effect=lambda: events.append("truststore")) as inject:
                # Check the result and order: download, trust store, then another download.
                self.assertEqual(self.os_wrapper.download_dataset(self.DATASET_NAME, self.OUTPUT_DIR), self.OUTPUT_DIR)
                self.assertEqual(events, ["download", "truststore", "download"])
                self.assertEqual(
                    download.call_args_list,
                    [
                        call(self.DATASET_NAME, output_dir=self.OUTPUT_DIR),
                        call(self.DATASET_NAME, output_dir=self.OUTPUT_DIR),
                    ],
                )
                inject.assert_called_once_with()

    def test_certificate_failure_after_retry_propagates(self):
        """Tests that a second SSL error propagates after one retry."""
        # Force both downloads to fail with SSL errors and intercept the fallback.
        with patch(omf.OS_DATASET_DOWNLOAD, side_effect=SSLError("CERTIFICATE_VERIFY_FAILED")) as download:
            with patch(omf.OS_TRUSTSTORE) as inject:
                # The error must not be suppressed after the retry.
                with self.assertRaises(SSLError):
                    self.os_wrapper.download_dataset(self.DATASET_NAME, self.OUTPUT_DIR)
                # Expect two attempts and a single trust store initialization.
                self.assertEqual(download.call_count, 2)
                inject.assert_called_once_with()

    def test_other_download_failures_do_not_enable_truststore(self):
        """Tests that non-certificate errors do not enable the SSL fallback."""
        # Try different errors: generic TLS, HTTP, and filesystem failures.
        for error in (SSLError("TLS handshake failed"), HTTPError("401 Unauthorized"), OSError("disk full")):
            with self.subTest(error=error):
                # Each error must propagate without a retry or trust store initialization.
                with patch(omf.OS_DATASET_DOWNLOAD, side_effect=error) as download:
                    with patch(omf.OS_TRUSTSTORE) as inject:
                        with self.assertRaises(type(error)):
                            self.os_wrapper.download_dataset(self.DATASET_NAME, self.OUTPUT_DIR)
                        download.assert_called_once_with(self.DATASET_NAME, output_dir=self.OUTPUT_DIR)
                        inject.assert_not_called()

    def test_interface_is_abstract(self):
        """Tests that the abstract OsManager interface cannot be instantiated."""
        with self.assertRaises(TypeError):
            src.OsManager()

    def test_os_path_operations(self):
        """Tests that dirname returns the result from the os library."""
        # Compare the wrapper result with the standard library result.
        wrapper: src.OsWrapper = src.OsWrapper()
        path: str = os.path.join("config", "config.ini")
        self.assertEqual(wrapper.dirname(path), os.path.dirname(path))

    def test_path_operations_delegate(self):
        """Tests that path operations are delegated to Path objects."""
        # Use both strings and Path objects and check each supported operation.
        wrapper: src.OsWrapper = src.OsWrapper()
        for path in ("config", Path("config")):
            for method in ("exists", "is_file", "is_dir", "iterdir", "unlink", "rmdir"):
                with self.subTest(path=path, method=method):
                    with patch(omf.OS_PATH) as path_class:
                        path_mock = path_class.return_value
                        result = getattr(wrapper, method)(path)
                        path_class.assert_called_once_with(path)
                        getattr(path_mock, method).assert_called_once_with()
                        if method in ("exists", "is_file", "is_dir", "iterdir"):
                            # Filesystem read methods return the value from Path.
                            self.assertIs(result, getattr(path_mock, method).return_value)
                        else:
                            # Mutating operations must not return a value.
                            self.assertIsNone(result)

    def test_mkdir_delegates_options(self):
        """Tests that mkdir passes the path and options to the Path library."""
        with patch(omf.OS_PATH) as path_class:
            self.os_wrapper.mkdir("config", parents=True, exist_ok=True)
            path_class.assert_called_once_with("config")
            path_class.return_value.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_filesystem_errors_propagate(self):
        """Tests that filesystem errors are not caught or suppressed."""
        # Simulate a permission error during unlink and verify that it propagates.
        with patch(omf.OS_PATH) as path_class:
            path_class.return_value.unlink.side_effect = PermissionError("denied")
            with self.assertRaises(PermissionError):
                self.os_wrapper.unlink("config.ini")
