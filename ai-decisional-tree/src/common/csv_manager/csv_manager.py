from abc import ABC, abstractmethod

import pandas as pd


class CsvManager(ABC):
    @abstractmethod
    def read(self, csv_file: str) -> pd.DataFrame:
        pass