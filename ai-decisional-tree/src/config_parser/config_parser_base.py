"""
@brief Read configuration values and translate parsing errors.
"""
import configparser

import src.common as cm
import src.config_parser.data_structures as ds
import src.config_parser.exceptions as ex


def config_error(func):
    """
    @brief Translate configuration parser errors raised by a wrapped accessor into application exceptions.
    @param func: Configuration accessor wrapped to translate errors.
    @return: The value produced by this operation.
    """
    def wrapper(self, *args, **kwargs):
        """
        @brief Perform the wrapper operation.
        @param args: Additional positional arguments.
        @param kwargs: Additional keyword arguments.
        @return: The value produced by this operation.
        @throws NoSectionError: If the operation encounters this error.
        @throws NoOptionError: If the operation encounters this error.
        @throws ConfigError: If the operation encounters this error.
        """
        try:
            return func(self, *args, **kwargs)
        except configparser.NoSectionError as err:
            raise ex.NoSectionError(err.section) from err
        except configparser.NoOptionError as err:
            raise ex.NoOptionError(err.option) from err
        except Exception as err:
            raise ex.ConfigError(str(err)) from err

    return wrapper


class ConfigParserBase:
    """
    @brief Load configuration and provide typed value accessors.
    """
    CHAR_TO_REMOVE: str = '"'

    def __init__(self, folder_manager: cm.FolderManager, config: None | configparser.ConfigParser = None):
        """
        @brief Load configuration values from the folder manager configuration file.
        @param folder_manager: Folder manager used for filesystem operations.
        @param config: Optional ConfigParser instance used for configuration values.
        """
        self._folder_manager: cm.FolderManager = folder_manager
        self._config_file: str = self._folder_manager.config_file_path
        self.config: configparser.ConfigParser = config or configparser.ConfigParser()
        self.config.read(self._config_file)

    def _remove_characters(self, value: str) -> str:
        """
        @brief Remove configured quote characters from a configuration value.
        @param value: String value to normalize.
        @return: The value with configured characters removed.
        """
        return value.replace(self.CHAR_TO_REMOVE, "")

    @config_error
    def get(self, section: ds.Section, option: ds.Option, to_remove: bool = True) -> str:
        """
        @brief Read a string option from a configuration section.
        @param section: Configuration section to read.
        @param option: Configuration option to read.
        @param to_remove: Whether to remove quote characters from the returned string.
        @return: The str produced by this operation.
        @throws NoSectionError: When the requested section is missing.
        @throws NoOptionError: When the requested option is missing.
        @throws ConfigError: When the value cannot be read or converted.
        """
        str_value: str = self.config.get(section, option)
        if to_remove:
            return self._remove_characters(str_value)
        return str_value

    @config_error
    def get_int(self, section: ds.Section, option: ds.Option) -> int:
        """
        @brief Read and convert an option to an integer.
        @param section: Configuration section to read.
        @param option: Configuration option to read.
        @return: The int produced by this operation.
        @throws NoSectionError: When the requested section is missing.
        @throws NoOptionError: When the requested option is missing.
        @throws ConfigError: When the value cannot be read or converted.
        """
        return self.config.getint(section, option)

    @config_error
    def get_float(self, section: ds.Section, option: ds.Option) -> float:
        """
        @brief Read and convert an option to a float.
        @param section: Configuration section to read.
        @param option: Configuration option to read.
        @return: The float produced by this operation.
        @throws NoSectionError: When the requested section is missing.
        @throws NoOptionError: When the requested option is missing.
        @throws ConfigError: When the value cannot be read or converted.
        """
        return self.config.getfloat(section, option)

    @config_error
    def get_boolean(self, section: ds.Section, option: ds.Option) -> bool:
        """
        @brief Read and convert an option to a boolean.
        @param section: Configuration section to read.
        @param option: Configuration option to read.
        @return: The bool produced by this operation.
        @throws NoSectionError: When the requested section is missing.
        @throws NoOptionError: When the requested option is missing.
        @throws ConfigError: When the value cannot be read or converted.
        """
        return self.config.getboolean(section, option)
