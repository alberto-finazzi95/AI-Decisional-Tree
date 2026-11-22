"""
@brief Download dataset files, validate summaries, and persist volume tables.
"""

import pandas as pd

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm
import src.data.data_loader.exceptions as ex


def _set_new_columns(summary_df: pd.DataFrame):
    """
    @brief Initialize derived path and subfolder columns in a summary DataFrame.
    @param summary_df: Dataset summary to update in place.
    """
    # Adding new columns to the summary DataFrame for file paths, subfolders, and number of subfolders
    summary_df[dcm.Feature.PATH] = ""
    summary_df[dcm.Feature.NUM_SUB] = 0
    summary_df[dcm.Feature.SUBFOLDERS] = ""


class DataLoader(dcm.BaseData):
    """
    @brief Load dataset metadata and validate study files.
    """

    SUB_FOLDER_PREFIX: str = "00"
    INVALID_VALUES: str = "unknown"
    TENTATIVES: int = 4
    DATASET_TYPES: tuple[dcm.DatasetType, ...] = (
        dcm.DatasetType.TRAIN,
        dcm.DatasetType.VALIDATION,
        dcm.DatasetType.TEST,
    )

    def __init__(
        self,
        folder_manager: cm.FolderManager,
        config_parser: cp.ConfigParser,
        csv_manager: cm.CsvManager | None = None,
        os_manager: cm.OsManager | None = None,
    ):
        """
        @brief Initialize dataset loading with optional CSV and filesystem helpers.
        @param folder_manager: Folder manager used for filesystem operations.
        @param config_parser: Parser providing dataset and output settings.
        @param csv_manager: Optional CSV reader implementation.
        @param os_manager: Optional filesystem-operation implementation.
        """
        super().__init__(
            folder_manager=folder_manager,
            config_parser=config_parser,
            os_manager=os_manager,
        )
        self._kaggle_dataset_name: str = self._config_parser.dataset_name
        self._csv_manager: cm.CsvManager | None = csv_manager if csv_manager is not None else cm.CsvManagerWrapper()

    def load_data(self) -> str:
        """
        @brief Reuse or download the configured dataset and return its extraction path.
        @return: The str produced by this operation.
        @throws DatasetLoadError: If the operation encounters this error.
        """
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
            except Exception as err:
                print(f"Attempt {tent + 1} failed with error: {err}")
        raise ex.DatasetLoadError(self._kaggle_dataset_name, self.TENTATIVES)

    def process_data(self):
        # Analyze the summary file
        """
        @brief Load summary metadata, validate dataset files, and build study catalogs.
        """
        self._load_summary()
        # Checking if all files are present in the dataset folder
        self._check_files()
        # Create a StudyCatalog for each dataset type
        self._create_study_catalogs()

    def _create_study_catalogs(self):
        """
        @brief Build a study catalog for each configured dataset split.
        """
        self._study_catalogs: dict[dcm.DatasetType, dcm.StudyCatalog] = {
            dataset_type: dcm.StudyCatalog(summary_df) for dataset_type, summary_df in self._SUMMARIES.items()
        }

    def get_all_study_catalog(self) -> dict[dcm.DatasetType, dcm.StudyCatalog]:
        """
        @brief Return the catalog containing all studies.
        @return: The dict[dcm.DatasetType, dcm.StudyCatalog] produced by this operation.
        """
        return self._study_catalogs

    def get_study_catalog(self, dataset_type: dcm.DatasetType) -> dcm.StudyCatalog:
        """
        @brief Return the catalog for a dataset split.
        @param dataset_type: Dataset split to process or retrieve.
        @return: The dcm.StudyCatalog produced by this operation.
        @throws StudyCatalogNotFound: If the operation encounters this error.
        """
        try:
            return self._study_catalogs[dataset_type]
        except KeyError as err:
            raise ex.StudyCatalogNotFound(dataset_type) from err

    def _get_summary(self, dataset_type: dcm.DatasetType) -> pd.DataFrame:
        """
        @brief Select summary rows for one dataset split and remove the split column.
        @param dataset_type: Dataset split whose rows should be selected.
        @return: A DataFrame containing only the selected split's study metadata.
        """
        return self._summary_csv_raw[self._summary_csv_raw[dcm.Feature.PART] == dataset_type].drop(
            columns=[dcm.Feature.PART]
        )

    def _load_summary(self):
        """
        @brief Read the summary CSV and partition its rows by dataset split.
        """
        self._summary_csv_raw: pd.DataFrame = pd.read_csv(self._summary_csv_path)
        # Replace the unknown vales with NaN to avoid issues with missing values
        self._summary_csv_raw.replace(self.INVALID_VALUES, pd.NA, inplace=True)
        print(
            f"Summary CSV loaded from {self._summary_csv_raw.shape[0]} rows and {self._summary_csv_raw.shape[1]} columns."
        )
        # Store the summaries in a dictionary for easy access
        self._SUMMARIES: dict[dcm.DatasetType, pd.DataFrame] = {
            data_type: self._get_summary(data_type) for data_type in self.DATASET_TYPES
        }

    def _set_file_path_in_summary(self, dataset_type: dcm.DatasetType, file_name: str, file_path: str):
        """
        @brief Store a resolved study directory path in its summary row.
        @param dataset_type: Dataset split containing the summary row.
        @param file_name: Study name used to locate the row.
        @param file_path: Resolved path to store.
        """
        summary_df: pd.DataFrame = self._SUMMARIES[dataset_type]
        summary_df.loc[summary_df[dcm.Feature.NAME] == file_name, dcm.Feature.PATH] = file_path

    def _get_data_path(self, data_name: str, dataset_type_folder: str | dcm.DatasetType) -> str:
        """
        @brief Compose a study path beneath its dataset-split directory.
        @param data_name: Study directory name.
        @param dataset_type_folder: Parent directory for the dataset split.
        @return: The composed study directory path.
        """
        return self.compose_path(
            dataset_type_folder,
            data_name,
        )

    def _get_dataset_type_folder(self, dataset_type: dcm.DatasetType) -> str:
        """
        @brief Compose the path to one dataset split beneath the dataset directory.
        @param dataset_type: Dataset split to locate.
        @return: The composed dataset-split directory path.
        """
        return self.compose_path(
            self._dataset_folder,
            dataset_type,
        )

    def _adding_subfolders_to_summary(self, dataset_type: dcm.DatasetType, dataset_name: str, file_path: str):
        """
        @brief Store sorted matching frame subfolders and their count in a summary row.
        @param dataset_type: Dataset split containing the summary row.
        @param dataset_name: Study name used to locate the row.
        @param file_path: Study directory whose subfolders are inspected.
        """
        subfolders: list[str] = sorted(
            [
                sub_folder
                for sub_folder in self._folder_manager.get_subfolders(file_path)
                if sub_folder.startswith(
                    self.SUB_FOLDER_PREFIX
                )  # Filter subfolders that start with the specified prefix
            ]
        )
        num_subfolders: int = len(subfolders)
        subfolders_str: str = ", ".join(subfolders)
        summary_df: pd.DataFrame = self._SUMMARIES[dataset_type]
        # Adding the number of subfolders to the summary DataFrame
        summary_df.loc[summary_df[dcm.Feature.NAME] == dataset_name, dcm.Feature.NUM_SUB] = num_subfolders
        # Adding the  subfolders to the summary DataFrame
        summary_df.loc[summary_df[dcm.Feature.NAME] == dataset_name, dcm.Feature.SUBFOLDERS] = subfolders_str

    def _check_files(self):
        """
        @brief Validate study directories for every split and raise on missing paths.
        @throws MissingFilesError: If any study directory is missing.
        """
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
        """
        @brief Validate study paths in one split and enrich its summary metadata.
        @param dataset_type: Dataset split being checked.
        @param summary_df: Summary rows for the split; updated with paths and subfolders.
        @return: List of study paths that do not exist.
        """
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
        """
        @brief Return the output directory for volumes in a dataset split.
        @param model_phase: Dataset split for the output.
        @return: The str produced by this operation.
        """
        return self.compose_path(
            self._dataset_output_folder_name,
            model_phase,
            cm.FolderName.VOLUMES,
        )

    def _get_patient_volume_path(self, patient_id: str, volumes_folder: str) -> str:
        """
        @brief Compose the Parquet output path for a patient's volume records.
        @param patient_id: Study identifier used in the output file name.
        @param volumes_folder: Directory where volume files are stored.
        @return: The composed Parquet file path.
        """
        return self.compose_path(
            volumes_folder,
            f"vol_{patient_id}_tabular.parquet",
        )

    def store_volume(self, df: pd.DataFrame, patient_id: str, model_phase: dcm.DatasetType):
        """
        @brief Save a patient volume DataFrame as a compressed Parquet file.
        @param df: DataFrame to save or process.
        @param patient_id: Study identifier.
        @param model_phase: Dataset split for the output.
        """
        volumes_folder: str = self.get_volumes_folder(model_phase)
        # Ensure the image path exists; if not, create it
        self._create_not_existing_folder(volumes_folder)
        volume_file_path: str = self._get_patient_volume_path(patient_id, volumes_folder)
        # Store the parquet file in the file system
        df.to_parquet(volume_file_path, compression="snappy", index=False)
        print(f"Volume saved successfully! Rows loaded: {len(df)} -> File: {volume_file_path}")
