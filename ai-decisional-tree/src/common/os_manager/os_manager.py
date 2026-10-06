from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

class OsManager(ABC):
    @abstractmethod
    def download_dataset(self, dataset_name: str, output_dir: str) -> str:
        pass

    @abstractmethod
    def dirname(self, path: str) -> str:
        pass

    @abstractmethod
    def exists(self, path: str | Path) -> bool:
        pass

    @abstractmethod
    def is_file(self, path: str | Path) -> bool:
        pass

    @abstractmethod
    def is_dir(self, path: str | Path) -> bool:
        pass

    @abstractmethod
    def mkdir(self, path: str | Path, parents: bool = False, exist_ok: bool = False) -> None:
        pass

    @abstractmethod
    def iterdir(self, path: str | Path) -> Iterator[Path]:
        pass

    @abstractmethod
    def unlink(self, path: str | Path) -> None:
        pass

    @abstractmethod
    def rmdir(self, path: str | Path) -> None:
        pass