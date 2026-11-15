"""
@brief Provide a pandas-backed implementation of the CSV reader.
"""
import pandas as pd

import src.common.csv_manager.csv_manager as cr


class CsvManagerWrapper(cr.CsvManager):
    """
    @brief Read CSV files with pandas.
    """
    def read(self, csv_file: str) -> pd.DataFrame:
        """
        @brief Read the specified CSV file with pandas and return its rows as a DataFrame.
        @param csv_file: Path to the CSV file.
        @return: The pd.DataFrame produced by this operation.
        """
        return pd.read_csv(csv_file)
