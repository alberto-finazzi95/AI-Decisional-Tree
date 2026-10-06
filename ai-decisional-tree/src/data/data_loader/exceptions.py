

class DatasetLoadError(RuntimeError):
    def __init__(self, dataset_name: str, tentatives: int):
        super().__init__(f"Failed to download dataset {dataset_name} after {tentatives} attempts.")
