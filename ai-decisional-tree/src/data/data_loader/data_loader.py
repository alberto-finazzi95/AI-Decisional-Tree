import pandas as pd

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm
import src.data.data_loader.exceptions as ex


class DataLoader(dcm.BaseData):
    TENTATIVES: int = 4

    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
            csv_manager: cm.CsvManager| None = None,
            os_manager: cm.OsManager | None = None,
    ):
        super().__init__(
            folder_manager=folder_manager,
            config_parser=config_parser,
            os_manager=os_manager,
        )
        self._kaggle_dataset_name: str = self._config_parser.dataset_name
        self._csv_manager: cm.CsvManager| None = csv_manager if csv_manager is not None else cm.CsvManagerWrapper()

    def load_data(self) -> str:
        if self.folder_exists(self._dataset_extract_path):
            print(f"Dataset found at {self._dataset_extract_path}. Skipping the download...")
            return self._dataset_extract_path
        print(f"Loading {self._kaggle_dataset_name} from Kaggle; completed downloads will be reused.")
        for tent in range(DataLoader.TENTATIVES):
            try:
                return self._os_manager.download_dataset(
                    self._kaggle_dataset_name,
                    self._dataset_extract_path,
                )
            except Exception as e:
                print(f"Attempt {tent + 1} failed with error: {e}")
        raise ex.DatasetLoadError(self._kaggle_dataset_name, self.TENTATIVES)

    def process_data(self):
        # Analyze the summary file
        self._load_summary()

    def _get_summary(self, dataset_type: dcm.DatasetType) -> pd.DataFrame:
        return self._summary_csv_raw[
            self._summary_csv_raw[dcm.Feature.PART] == dataset_type
        ].drop(columns=[dcm.Feature.PART])

    def _load_summary(self):
        self._summary_csv_raw: pd.DataFrame = pd.read_csv(self._summary_csv_path)
        print(f"Summary CSV loaded from {self._summary_csv_raw.shape[0]} rows and {self._summary_csv_raw.shape[1]} columns.")
        self._training_summary: pd.DataFrame = self._get_summary(dcm.DatasetType.TRAIN)
        self._validation_summary: pd.DataFrame = self._get_summary(dcm.DatasetType.VALIDATION)
        self._test_summary: pd.DataFrame = self._get_summary(dcm.DatasetType.TEST)
