from enum import StrEnum
from unittest.mock import Mock

import src.common as src
import src.config_parser as cp


class OsMockFolder(StrEnum):
    """Stores import paths used to replace OS dependencies in tests."""

    # Location where OsWrapper constructs Path objects.
    OS_PATH = "src.common.os_manager.os_wrapper.Path"
    # Location where OsWrapper opens ZIP archives.
    OS_ZIPFILE = "src.common.os_manager.os_wrapper.zipfile.ZipFile"
    # Location where FolderManager constructs the operating system wrapper.
    OS_WRAPPER = "src.common.folder_manager.folder_manager_base.OsWrapper"
    # External function that downloads a Kaggle dataset.
    OS_DATASET_DOWNLOAD = "src.common.os_manager.os_wrapper.kagglehub.dataset_download"
    # Function that enables the system trust store for SSL certificates.
    OS_TRUSTSTORE = "src.common.os_manager.os_wrapper.truststore.inject_into_ssl"


"""Shared dependency setup for tests of the data-processing components."""


def make_data_dependencies():
    """Return filesystem, folder, and configuration dependencies isolated from disk."""
    os_manager: Mock = Mock(spec_set=src.OsManager)
    os_manager.exists.return_value = True
    os_manager.is_dir.return_value = True
    os_manager.is_file.return_value = True

    folder_manager: src.FolderManager = src.FolderManager("../", os_manager)
    config_parser: cp.ConfigParser = cp.ConfigParser(folder_manager)
    config_parser.config.read_dict(
        {
            "Dataset": {"name": "owner/dataset", "output_path": "extracted"},
            "Storing data": {
                "save img": "true",
                "save video": "true",
                "save img filtered": "false",
                "save video filtered": "false",
            },
        }
    )
    return os_manager, folder_manager, config_parser
