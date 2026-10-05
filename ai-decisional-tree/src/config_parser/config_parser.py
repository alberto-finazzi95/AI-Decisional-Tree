import src.common as cm
import src.config_parser.config_parser_base as cpb
import src.config_parser.data_structures as ds


class ConfigParser(cpb.ConfigParserBase):
    def __init__(self, folder_manager: cm.FolderManager):
        super().__init__(folder_manager)

    @property
    def dataset_name(self) -> str:
        return self.get(ds.Section.DATASET, ds.Option.NAME)

    @property
    def dataset_output_path(self) -> str:
        return self.get(ds.Section.DATASET, ds.Option.OUTPUT_PATH)
