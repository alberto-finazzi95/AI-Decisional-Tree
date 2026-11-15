"""
@brief Define errors raised while reading configuration settings.
"""
import src.config_parser.data_structures as ds


class NoSectionError(ValueError):
    """
    @brief Raised when a requested configuration section is missing.
    """
    def __init__(self, section: str | ds.Section):
        """
        @brief Create a configuration error identifying the missing section.
        @param section: Configuration section to read.
        """
        super().__init__(f"Section not found in config file: {section}")


class NoOptionError(ValueError):
    """
    @brief Raised when a requested configuration option is missing.
    """
    def __init__(self, option: str | ds.Option):
        """
        @brief Create a configuration error identifying the missing option.
        @param option: Configuration option to read.
        """
        super().__init__(f"Option not found in config file: {option}")


class ConfigError(Exception):
    """
    @brief Raised when a configuration value cannot be read or converted.
    """
    def __init__(self, error: str):
        """
        @brief Create a configuration error with the underlying error message.
        @param error: Underlying configuration error message.
        """
        super().__init__(f"Error reading config file: {error}")
