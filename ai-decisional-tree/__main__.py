import os
import sys

import __version__ as v
import src

if __name__ == "__main__":
    print(f"Running SW version: {v.VERSION}")
    current_folder: str = os.path.dirname(os.path.abspath(sys.argv[0]))

    folder_manager: src.FolderManager = src.FolderManager(current_folder)
    config_parser: src.ConfigParser = src.ConfigParser(folder_manager)
    data_loader: src.DataLoader = src.DataLoader(
        folder_manager=folder_manager,
        config_parser=config_parser,
    )