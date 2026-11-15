"""
@brief Define the abstract interface for reading CSV files.
"""
from abc import ABC, abstractmethod

import pandas as pd


class CsvManager(ABC):
    """
    @brief Abstract interface for reading a CSV file into a DataFrame.
    """
    @abstractmethod
    def read(self, csv_file: str) -> pd.DataFrame:
        """
        @brief Read a CSV file into a pandas DataFrame.
        @param csv_file: Path to the CSV file.
        @return: The pd.DataFrame produced by this operation.
        """
        pass
