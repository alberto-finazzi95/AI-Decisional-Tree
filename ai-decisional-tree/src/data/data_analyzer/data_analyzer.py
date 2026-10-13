from __future__ import annotations

from typing import TYPE_CHECKING

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm

if TYPE_CHECKING:
    import pandas as pd


class DataAnalyzer(dcm.BaseData):
    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
            os_manager: cm.OsManager | None = None,
            csv_reader: dcm.CsvReader | None = None,
    ):
        super().__init__(
            folder_manager=folder_manager,
            config_parser=config_parser,
            os_manager=os_manager
        )
        self._csv_reader: dcm.CsvReader = csv_reader if csv_reader is not None else dcm.CsvReader()

    def analyze(self) -> pd.DataFrame:
        return self._csv_reader.read_csv(self._summary_csv_path)