import pandas as pd

import src.common.csv_manager.csv_manager as cr


class CsvManagerWrapper(cr.CsvManager):
    def read(self, csv_file: str) -> pd.DataFrame:
        return pd.read_csv(csv_file)
