import src.common as cm
import src.config_parser as cp
import src.data_loader.exceptions as ex


class DataLoader:
    TENTATIVES: int = 4
    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
            os_manager: cm.OsManager | None = None
    ):
        self._folder_manager: cm.FolderManager = folder_manager
        self._config_parser: cp.ConfigParser = config_parser
        self._os_manager: cm.OsManager = os_manager if os_manager is not None else cm.OsWrapper()
        self._kaggle_dataset_name: str = self._config_parser.dataset_name
        self._dataset_name: str = self._config_parser.dataset_output_path
        self._dataset_extract_path: str = self._folder_manager.get_folder_path(
            folder_name=self._config_parser.dataset_output_path,
            str_format=True,
        )

    def folder_exists(self, folder_path: str) -> bool:
        return self._os_manager.exists(folder_path) and self._os_manager.is_dir(folder_path)

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
