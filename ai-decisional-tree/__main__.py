import os
import sys

import __version__ as v
import src


if __name__ == "__main__":
    print(f"Running SW version: {v.VERSION}")
    current_folder: str = os.path.dirname(os.path.abspath(sys.argv[0]))

    os_manager: src.OsManager = src.OsWrapper()
    folder_manager: src.FolderManager = src.FolderManager(current_folder, os_manager)
    config_parser: src.ConfigParser = src.ConfigParser(folder_manager)

    data_toolkit: src.DataToolkit = src.DataToolkit(
        os_manager=os_manager,
        folder_manager=folder_manager,
        config_parser=config_parser,
    )

    # Data Manager to handle data operations
    data_manager: src.DataManager = src.DataManager(
        data_toolkit=data_toolkit,
    )

    # For all patients
    for state in src.DatasetType:
        # For train, val and test set
        data_manager.state = state
        # Plot all raw TACs as images and videos
        data_manager.create_all_tacs()
        # Plot all filtered TACs as images and videos
        data_manager.create_all_tacs_filtered()
        # Create the volumes files for the model
        data_manager.create_volume_tacs()
