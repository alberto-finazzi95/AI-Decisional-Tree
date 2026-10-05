import src.config_parser.data_structures as ds


class NoSectionError(ValueError):
    def __init__(self, section: str | ds.Section):
        super().__init__(f"Section not found in config file: {section}")


class NoOptionError(ValueError):
    def __init__(self, option: str | ds.Option):
        super().__init__(f"Option not found in config file: {option}")


class ConfigError(Exception):
    def __init__(self, error: str):
        super().__init__(f"Error reading config file: {error}")
