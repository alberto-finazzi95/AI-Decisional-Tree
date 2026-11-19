"""
@brief Define errors raised during dataset download and validation.
"""

import src.data.common as dcm


class DatasetLoadError(RuntimeError):
    """
    @brief Raised when dataset download attempts are exhausted.
    """

    def __init__(self, dataset_name: str, tentatives: int):
        """
        @brief Create an error identifying a dataset download that exhausted its attempts.
        @param dataset_name: Dataset identifier to download.
        @param tentatives: Number of attempted downloads.
        """
        super().__init__(f"Failed to download dataset {dataset_name} after {tentatives} attempts.")


class MissingFilesError(FileNotFoundError):
    """
    @brief Raised when expected dataset files are missing.
    """

    def __init__(self, dataset_type: dcm.DatasetType, missing_files: list):
        """
        @brief Create an error listing files missing from a dataset split.
        @param dataset_type: Dataset split to process or retrieve.
        @param missing_files: Paths that were not found.
        """
        super().__init__(f"Missing files for {dataset_type.value} dataset: {missing_files}")


class StudyCatalogNotFound(KeyError):
    """
    @brief Raised when a study catalog for a split is unavailable.
    """

    def __init__(self, dataset_type: dcm.DatasetType):
        """
        @brief Create an error identifying the split without a study catalog.
        @param dataset_type: Dataset split to process or retrieve.
        """
        super().__init__(f"Study catalog not found for dataset type: {dataset_type.value}")
