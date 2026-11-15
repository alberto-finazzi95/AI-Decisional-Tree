from enum import StrEnum


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
