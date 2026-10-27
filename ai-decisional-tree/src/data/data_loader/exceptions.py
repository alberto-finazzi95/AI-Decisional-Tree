import src.data.common as dcm


class DatasetLoadError(RuntimeError):
    def __init__(self, dataset_name: str, tentatives: int):
        super().__init__(f"Failed to download dataset {dataset_name} after {tentatives} attempts.")


class MissingFilesError(FileNotFoundError):
    def __init__(self, dataset_type: dcm.DatasetType, missing_files: list):
        super().__init__(f"Missing files for {dataset_type.value} dataset: {missing_files}")


class StudyCatalogNotFound(KeyError):
    def __init__(self, dataset_type: dcm.DatasetType):
        super().__init__(f"Study catalog not found for dataset type: {dataset_type.value}")
