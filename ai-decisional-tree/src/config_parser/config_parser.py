"""
@brief Expose typed access to application configuration settings.
"""

import src.common as cm
import src.config_parser.config_parser_base as cpb
import src.config_parser.data_structures as ds


class ConfigParser(cpb.ConfigParserBase):
    """
    @brief Expose dataset and storage settings from the configuration file.
    """

    def __init__(self, folder_manager: cm.FolderManager):
        """
        @brief Load configuration settings from the file resolved by the folder manager.
        @param folder_manager: Folder manager used for filesystem operations.
        """
        super().__init__(folder_manager)

    @property
    def dataset_name(self) -> str:
        """
        @brief Return the configured dataset identifier.
        @return: The str produced by this operation.
        @throws NoSectionError: When the dataset section is missing.
        @throws NoOptionError: When the dataset name option is missing.
        @throws ConfigError: When the value cannot be read.
        """
        return self.get(ds.Section.DATASET, ds.Option.NAME)

    @property
    def dataset_output_path(self) -> str:
        """
        @brief Return the configured dataset output directory.
        @return: The str produced by this operation.
        @throws NoSectionError: When the dataset section is missing.
        @throws NoOptionError: When the output path option is missing.
        @throws ConfigError: When the value cannot be read.
        """
        return self.get(ds.Section.DATASET, ds.Option.OUTPUT_PATH)

    @property
    def save_img(self) -> bool:
        """
        @brief Return whether raw TAC images should be saved.
        @return: The bool produced by this operation.
        @throws NoSectionError: When the storage section is missing.
        @throws NoOptionError: When the save-image option is missing.
        @throws ConfigError: When the value cannot be read or converted.
        """
        return self.get_boolean(ds.Section.STORAGE, ds.Option.SAVE_IMG)

    @property
    def save_video(self) -> bool:
        """
        @brief Return whether raw TAC videos should be saved.
        @return: The bool produced by this operation.
        @throws NoSectionError: When the storage section is missing.
        @throws NoOptionError: When the save-video option is missing.
        @throws ConfigError: When the value cannot be read or converted.
        """
        return self.get_boolean(ds.Section.STORAGE, ds.Option.SAVE_VIDEO)

    @property
    def save_img_flt(self) -> bool:
        """
        @brief Return whether filtered TAC images should be saved.
        @return: The bool produced by this operation.
        @throws NoSectionError: When the storage section is missing.
        @throws NoOptionError: When the save-filtered-image option is missing.
        @throws ConfigError: When the value cannot be read or converted.
        """
        return self.get_boolean(ds.Section.STORAGE, ds.Option.SAVE_IMG_FILT)

    @property
    def save_video_flt(self) -> bool:
        """
        @brief Return whether filtered TAC videos should be saved.
        @return: The bool produced by this operation.
        @throws NoSectionError: When the storage section is missing.
        @throws NoOptionError: When the save-filtered-video option is missing.
        @throws ConfigError: When the value cannot be read or converted.
        """
        return self.get_boolean(ds.Section.STORAGE, ds.Option.SAVE_VIDEO_FILT)
