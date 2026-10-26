import pandas as pd

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm
import src.data.data_loader.exceptions as ex


def _set_new_columns(summary_df: pd.DataFrame):
    # Adding new columns to the summary DataFrame for file paths, subfolders, and number of subfolders
    summary_df[dcm.Feature.PATH] = ""
    summary_df[dcm.Feature.NUM_SUB] = 0
    summary_df[dcm.Feature.SUBFOLDERS] = ""


class DataLoader(dcm.BaseData):
    SUB_FOLDER_PREFIX: str = "00"
    TENTATIVES: int = 4
    DATASET_TYPES: tuple[dcm.DatasetType] =(
        dcm.DatasetType.TRAIN,
        dcm.DatasetType.VALIDATION,
        dcm.DatasetType.TEST,
    )

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
        # Create a StudyCatalog for each dataset type
        self._create_study_catalogs()

    def _create_study_catalogs(self):
        self._study_catalogs: dict[dcm.DatasetType, dcm.StudyCatalog] = {
            dataset_type: dcm.StudyCatalog(summary_df)
            for dataset_type, summary_df in self._SUMMARIES.items()
        }

    def get_study_catalog(self, dataset_type: dcm.DatasetType) -> dcm.StudyCatalog:
        try:
            return self._study_catalogs[dataset_type]
        except KeyError:
            raise ex.StudyCatalogNotFound(dataset_type)

    def _get_summary(self, dataset_type: dcm.DatasetType) -> pd.DataFrame:
        return self._summary_csv_raw[
            self._summary_csv_raw[dcm.Feature.PART] == dataset_type
        ].drop(columns=[dcm.Feature.PART])

    def _load_summary(self):
        self._summary_csv_raw: pd.DataFrame = pd.read_csv(self._summary_csv_path)
        print(f"Summary CSV loaded from {self._summary_csv_raw.shape[0]} rows and {self._summary_csv_raw.shape[1]} columns.")
        # Store the summaries in a dictionary for easy access
        self._SUMMARIES: dict[dcm.DatasetType, pd.DataFrame] = {
            data_type: self._get_summary(data_type) for data_type in self.DATASET_TYPES
        }

    def _set_file_path_in_summary(self, dataset_type: dcm.DatasetType, file_name: str, file_path: str):
        summary_df: pd.DataFrame = self._SUMMARIES[dataset_type]
        summary_df.loc[
            summary_df[dcm.Feature.NAME] == file_name, dcm.Feature.PATH
        ] = file_path

    def _get_data_path(self, data_name: str, dataset_type_folder: dcm.DatasetType) -> str:
        return self.compose_path(
                    dataset_type_folder,
                    data_name,
                )

    def _get_dataset_type_folder(self, dataset_type: dcm.DatasetType) -> str:
        return self.compose_path(
            self._dataset_folder,
            dataset_type
        )

    def _adding_subfolders_to_summary(self, dataset_type: dcm.DatasetType, dataset_name: str, file_path: str):
        subfolders: list[str] = sorted(
            [
                sub_folder for sub_folder in self._folder_manager.get_subfolders(file_path)
                if sub_folder.startswith(self.SUB_FOLDER_PREFIX)  # Filter subfolders that start with the specified prefix
            ]
        )
        num_subfolders: int = len(subfolders)
        subfolders_str: str = ", ".join(subfolders)
        summary_df: pd.DataFrame = self._SUMMARIES[dataset_type]
        # Adding the number of subfolders to the summary DataFrame
        summary_df.loc[
            summary_df[dcm.Feature.NAME] == dataset_name, dcm.Feature.NUM_SUB
        ] = num_subfolders
        # Adding the  subfolders to the summary DataFrame
        summary_df.loc[
            summary_df[dcm.Feature.NAME] == dataset_name, dcm.Feature.SUBFOLDERS
        ] = subfolders_str  # Store the list of subfolders in the DataFrame

    def _check_files(self):
        for dataset_type, summary_df in self._SUMMARIES.items():
            print(f"Checking files for {dataset_type.value} dataset with {summary_df.shape[0]} entries.")
            # Check and update the summary DataFrame with the full paths of the files, and collect missing files
            missing_files = self._check_dataset_type(dataset_type, summary_df)
            if missing_files:
                raise ex.MissingFilesError(dataset_type, missing_files)

    def _check_dataset_type(
            self,
            dataset_type: dcm.DatasetType,
            summary_df: pd.DataFrame,
    ) -> list:
        missing_files: list = []
        dataset_type_folder: str = self._get_dataset_type_folder(dataset_type)
        # Setting the number of subfolders column to integer type to avoid issues with NaN values
        _set_new_columns(summary_df)
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

    def get_volumes_folder(self, model_phase: dcm.DatasetType) -> str:
        return self.compose_path(
            self._dataset_output_folder_name,
            model_phase,
            cm.FolderName.VOLUMES,
        )

    def _get_patient_volume_path(self, patient_id: str, volumes_folder: str) -> str:
        return self.compose_path(
            volumes_folder,
            f"vol_{patient_id}_tabular.parquet"
        )

    def store_volume(self, df: pd.DataFrame, patient_id: str, model_phase: dcm.DatasetType):
        volumes_folder: str = self.get_volumes_folder(model_phase)
        # Ensure the image path exists; if not, create it
        self._create_not_existing_folder(volumes_folder)
        volume_file_path: str = self._get_patient_volume_path(patient_id, volumes_folder)
        # Store the parquet file in the file system
        df.to_parquet(volume_file_path, compression='snappy', index=False)
        print(f"Volume saved successfully! Rows loaded: {len(df)} -> File: {volume_file_path}")
