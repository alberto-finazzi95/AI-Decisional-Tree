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
        # Checking if all files are present in the dataset folder
        self._check_files()

    def _get_summary(self, dataset_type: dcm.DatasetType) -> pd.DataFrame:
        return self._summary_csv_raw[
            self._summary_csv_raw[dcm.Feature.PART] == dataset_type
        ].drop(columns=[dcm.Feature.PART])

    def _load_summary(self):
        self._summary_csv_raw: pd.DataFrame = pd.read_csv(self._summary_csv_path)
        print(f"Summary CSV loaded from {self._summary_csv_raw.shape[0]} rows and {self._summary_csv_raw.shape[1]} columns.")
        # Create separate DataFrames for training, validation, and test datasets
        self._training_summary: pd.DataFrame = self._get_summary(dcm.DatasetType.TRAIN)
        self._validation_summary: pd.DataFrame = self._get_summary(dcm.DatasetType.VALIDATION)
        self._test_summary: pd.DataFrame = self._get_summary(dcm.DatasetType.TEST)
        # Store the summaries in a dictionary for easy access
        self.SUMMARIES: dict[dcm.DatasetType, pd.DataFrame] = {
            dcm.DatasetType.TRAIN: self._training_summary,
            dcm.DatasetType.VALIDATION: self._validation_summary,
            dcm.DatasetType.TEST: self._test_summary,
        }

    def _set_file_path_in_summary(self, dataset_type: dcm.DatasetType, file_name: str, file_path: str):
        summary_df: pd.DataFrame = self.SUMMARIES[dataset_type]
        summary_df.loc[
            summary_df[dcm.Feature.NAME] == file_name, dcm.Feature.PATH
        ] = file_path

    def _get_data_path(self, data_name: str, dataset_type_folder: dcm.DatasetType) -> str:
        return self._folder_manager.compose_folders(
                    dataset_type_folder,
                    data_name,
                    str_format=True
                )

    def _get_dataset_type_folder(self, dataset_type: dcm.DatasetType) -> str:
        return self._folder_manager.compose_folders(
            self._dataset_folder,
            dataset_type,
            str_format=True
        )

    def _adding_subfolders_to_summary(self, dataset_type: dcm.DatasetType, dataset_name: str, file_path: str):
        subfolders: list[str] = sorted(self._folder_manager.get_subfolders(file_path))
        num_subfolders: int = len(subfolders)
        subfolders_str: str = ", ".join(subfolders)
        summary_df: pd.DataFrame = self.SUMMARIES[dataset_type]
        # Adding the number of subfolders to the summary DataFrame
        summary_df.loc[
            summary_df[dcm.Feature.NAME] == dataset_name, dcm.Feature.NUM_SUB
        ] = num_subfolders
        # Adding the  subfolders to the summary DataFrame
        summary_df.loc[
            summary_df[dcm.Feature.NAME] == dataset_name, dcm.Feature.SUBFOLDERS
        ] = subfolders_str  # Store the list of subfolders in the DataFrame

    def _check_files(self):
        for dataset_type, summary_df in self.SUMMARIES.items():
            print(f"Checking files for {dataset_type.value} dataset with {summary_df.shape[0]} entries.")
            # Check and update the summary DataFrame with the full paths of the files, and collect missing files
            missing_files = self._check_dataset_type(dataset_type, summary_df)
            if missing_files:
                raise ex.MissingFilesError(dataset_type, missing_files)

    def _set_new_columns(self, summary_df: pd.DataFrame):
        # Adding new columns to the summary DataFrame for file paths, subfolders, and number of subfolders
        summary_df[dcm.Feature.PATH] = ""
        summary_df[dcm.Feature.NUM_SUB] = 0
        summary_df[dcm.Feature.SUBFOLDERS] = ""

    def _check_dataset_type(
            self,
            dataset_type: dcm.DatasetType,
            summary_df: pd.DataFrame,
    ) -> list:
        missing_files: list = []
        dataset_type_folder: str = self._get_dataset_type_folder(dataset_type)
        # Setting the number of subfolders column to integer type to avoid issues with NaN values
        self._set_new_columns(summary_df)
        for _, row in summary_df.iterrows():
            data_name: str = row[dcm.Feature.NAME]
            data_path: str = self._get_data_path(data_name, dataset_type_folder)
            if not self._os_manager.exists(data_path):
                missing_files.append(data_path)
                continue
            # Adding to the summary DataFrame the full path of the file for future reference
            self._set_file_path_in_summary(dataset_type, data_name, data_path)
            # Adding the subfolders as a list
            self._adding_subfolders_to_summary(dataset_type, data_name, data_path)
        return missing_files

