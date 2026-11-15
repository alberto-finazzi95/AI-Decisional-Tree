import unittest
from pathlib import Path
from unittest.mock import Mock, patch, call

import src as src
from src.common.folder_manager import FolderManager
from src.common.folder_manager.data_structures import FileName, FolderName
from tests.helper import OsMockFolder as omf



class FolderManagerTests(unittest.TestCase):
    """Tests that FolderManager builds paths and delegates OS operations."""

    def setUp(self):
        """Creates a folder manager connected to a mocked operating system manager."""
        # The mock allows operations to be checked without modifying the disk.
        self.os_manager: Mock = Mock(spec_set=src.OsManager)
        self.base_path: Path = Path("application")
        self.manager = FolderManager(str(self.base_path), self.os_manager)

    def test_default_wrapper_preserves_existing_constructor(self):
        """Tests that the constructor still uses the default wrapper when none is provided."""
        # Replace the real wrapper and check which folder the manager inspects.
        with patch(omf.OS_WRAPPER) as wrapper:
            manager: FolderManager = FolderManager("application")
            manager.folder_exists(FolderName.CONFIG)
            wrapper.return_value.exists.assert_called_once_with(Path("application") / "config")

    def test_file_exists_uses_injected_manager(self):
        """Tests that file checks use the injected manager and the full path."""
        # Build the expected path and simulate an existing file.
        path: Path = self.base_path / FolderName.CONFIG / FileName.CONFIG
        self.os_manager.exists.return_value = True
        self.os_manager.is_file.return_value = True
        # Check the result and the arguments passed to the manager.
        self.assertTrue(self.manager.file_exists(FolderName.CONFIG, FileName.CONFIG))
        self.os_manager.exists.assert_called_once_with(path)
        self.os_manager.is_file.assert_called_once_with(path)

    def test_missing_file_short_circuits(self):
        """Tests that a missing path is not subsequently checked as a file."""
        # Report that the path is missing and verify the negative result.
        self.os_manager.exists.return_value = False
        self.assertFalse(self.manager.file_exists(FolderName.CONFIG, FileName.CONFIG))
        # The second check is unnecessary and must be skipped.
        self.os_manager.is_file.assert_not_called()

    def test_folder_exists_uses_injected_manager(self):
        """Tests that folder checks use the injected manager."""
        # Simulate the path as an existing directory.
        self.os_manager.exists.return_value = True
        self.os_manager.is_dir.return_value = True
        # The check must succeed for the configured full path.
        self.assertTrue(self.manager.folder_exists(FolderName.CONFIG))
        self.os_manager.is_dir.assert_called_once_with(self.base_path / FolderName.CONFIG)

    def test_create_folder_uses_injected_manager(self):
        """Tests that folder creation delegates mkdir with the required options."""
        # Create the logical folder and check the path and options passed to the mock.
        self.manager.create_folder(FolderName.CONFIG)
        self.os_manager.mkdir.assert_called_once_with(
            self.base_path / FolderName.CONFIG,
            parents=True,
            exist_ok=True,
        )

    def test_delete_nested_folder_uses_full_paths(self):
        """Tests recursive deletion of a file and its nested folders."""
        # Define the paths to delete and simulate the hierarchy as existing.
        folder: Path = self.base_path / FolderName.CONFIG
        nested: Path = folder / "nested"
        file_path: Path = nested / "config.ini"
        self.os_manager.exists.return_value = True
        self.os_manager.is_dir.return_value = True
        self.os_manager.iterdir.side_effect = lambda path: iter(
            {
                folder: [nested],
                nested: [file_path],
            }[path]
        )
        self.os_manager.is_file.side_effect = lambda path: path == file_path

        # Delete the folder; the mocks provide the entries found at each level.
        self.manager.delete_folder(FolderName.CONFIG)

        # Check that the file and folders are removed, starting at the innermost level.
        self.os_manager.unlink.assert_called_once_with(file_path)
        self.assertEqual(self.os_manager.iterdir.call_args_list, [call(folder), call(nested)])
        self.assertEqual(self.os_manager.rmdir.call_args_list, [call(nested), call(folder)])

    def test_delete_missing_folder_does_not_modify_filesystem(self):
        """Tests that deleting a missing folder performs no filesystem operations."""
        # Simulate a missing folder and request its deletion.
        self.os_manager.exists.return_value = False
        self.manager.delete_folder(FolderName.CONFIG)
        # No contents should be enumerated or removed.
        self.os_manager.iterdir.assert_not_called()
        self.os_manager.unlink.assert_not_called()
        self.os_manager.rmdir.assert_not_called()
