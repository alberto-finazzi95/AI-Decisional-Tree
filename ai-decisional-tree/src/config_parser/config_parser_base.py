from abc import ABC
import configparser

import src.common as cm
import src.config_parser.exceptions as ex
import src.config_parser.data_structures as ds


def config_error(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except configparser.NoSectionError as e:
            raise ex.NoSectionError(e.section)
        except configparser.NoOptionError as e:
            raise ex.NoOptionError(e.option)
        except Exception as e:
            raise ex.ConfigError(str(e))
    return wrapper


class ConfigParserBase(ABC):
    CHAR_TO_REMOVE: str = '\"'

    def __init__(self, folder_manager: cm.FolderManager, config: None | configparser.ConfigParser = None):
        self._folder_manager: cm.FolderManager = folder_manager
        self._config_file: str = self._folder_manager.config_file_path
        self.config: configparser.ConfigParser = config or configparser.ConfigParser()
        self.config.read(self._config_file)

    def _remove_characters(self, value: str) -> str:
        return value.replace(self.CHAR_TO_REMOVE, '')

    @config_error
    def get(self, section: ds.Section, option: ds.Option, to_remove: bool = True) -> str:
        str_value: str = self.config.get(section, option)
        if to_remove:
            return self._remove_characters(str_value)
        return str_value

    @config_error
    def get_int(self, section: ds.Section, option: ds.Option) -> int:
        return self.config.getint(section, option)

    @config_error
    def get_float(self, section: ds.Section, option: ds.Option) -> float:
        return self.config.getfloat(section, option)

    @config_error
    def get_boolean(self, section: ds.Section, option: ds.Option) -> bool:
        return self.config.getboolean(section, option)