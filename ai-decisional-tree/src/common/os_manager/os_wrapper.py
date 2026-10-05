import os
import subprocess
import zipfile
import zlib
from collections.abc import Iterator
from pathlib import Path

import kagglehub
import truststore
from requests.exceptions import SSLError

import src.common.os_manager as osm


class OsWrapper(osm.OsManager):
    def download_dataset(self, dataset_name: str, output_dir: str) -> str:
        try:
            return kagglehub.dataset_download(dataset_name, output_dir=output_dir)
        except SSLError as error:
            if "CERTIFICATE_VERIFY_FAILED" not in str(error):
                raise
            print("Certificate verification failed; retrying with system certificates.")
            truststore.inject_into_ssl()
            return kagglehub.dataset_download(dataset_name, output_dir=output_dir)

    def system(self, command_list: list[str]) -> int:
        return subprocess.run(command_list, check=True).returncode

    def abspath(self, path: str) -> str:
        return os.path.abspath(path)

    def dirname(self, path: str) -> str:
        return os.path.dirname(path)

    def exists(self, path: str | Path) -> bool:
        return Path(path).exists()

    def is_file(self, path: str | Path) -> bool:
        return Path(path).is_file()

    def is_valid_zip(self, path: str | Path) -> bool:
        try:
            with zipfile.ZipFile(path) as archive:
                return archive.testzip() is None
        except (zipfile.BadZipFile, zlib.error):
            return False

    def is_dir(self, path: str | Path) -> bool:
        return Path(path).is_dir()

    def mkdir(self, path: str | Path, parents: bool = False, exist_ok: bool = False) -> None:
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def iterdir(self, path: str | Path) -> Iterator[Path]:
        return Path(path).iterdir()

    def unlink(self, path: str | Path) -> None:
        Path(path).unlink()

    def rmdir(self, path: str | Path) -> None:
        Path(path).rmdir()