from enum import StrEnum


class OsMockFolder(StrEnum):
    OS_PATH = "src.common.os_manager.os_wrapper.Path"
    OS_ZIPFILE = "src.common.os_manager.os_wrapper.zipfile.ZipFile"
    OS_WRAPPER = "src.common.folder_manager.folder_manager_base.OsWrapper"
    OS_DATASET_DOWNLOAD = "src.common.os_manager.os_wrapper.kagglehub.dataset_download"
    OS_TRUSTSTORE = "src.common.os_manager.os_wrapper.truststore.inject_into_ssl"
