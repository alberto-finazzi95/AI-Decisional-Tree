"""
@brief Provide application-specific folder paths on top of FolderManagerBase.
"""

from pathlib import Path

import src.common.folder_manager.data_structures as ds
import src.common.folder_manager.folder_manager_base as fmb
import src.common.os_manager as osm


class FolderManager(fmb.FolderManagerBase):
    """
    @brief Resolve application directories and the configuration file.
    """

    def __init__(self, base_path: str, os_manager: osm.OsManager | None = None):
        """
        @brief Initialize path operations relative to the application base directory.
        @param base_path: Base directory used to compose paths.
        @param os_manager: Optional filesystem-operation implementation.
        """
        super().__init__(base_path, os_manager)

    @property
    def config_file_path(self) -> str | Path:
        """
        @brief Return the path to the configured application settings file.
        @return: The str | Path produced by this operation.
        """
        return self.get_file_path_if_exist(ds.FolderName.CONFIG, ds.FileName.CONFIG)
