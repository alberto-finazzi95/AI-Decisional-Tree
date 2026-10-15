import src.common as cm
import src.config_parser as cp
import src.data.common as dcm
import src.data.data_loader as dl
import src.data.data_plotter as dp
import src.data.data_analyzer as da
import src.data.data_toolkit as dt


class DataManager:
    """
    A class to manage data loading, plotting, and analysis.

    Attributes:
        _data_loader (DataLoader): An instance of the DataLoader class.
        _data_plotter (DataPlotter): An instance of the DataPlotter class.
        _data_analyzer (DataAnalyzer): An instance of the DataAnalyzer class.
    """

    def __init__(
            self,
            folder_manager: cm.FolderManager,
            data_toolkit: dt.DataToolkit,
    ):
        """
        Initializes the DataManager with instances of DataLoader, DataPlotter, and DataAnalyzer.

        Args:
            folder_manager (FolderManager): An instance of the FolderManager class.
            data_toolkit (DataToolkit): An instance of the DataToolkit class.
        """
        # Initialize the base class with the provided folder manager and config parser
        self._folder_manager: cm.FolderManager = data_toolkit.folder_manager
        self._config_parser:  cp.ConfigParser = data_toolkit.config_parser

        # Get initial flags
        self._create_img: bool = self._config_parser.save_img
        self._create_video: bool = self._config_parser.save_video

        # Initialize the DataLoader, DataPlotter, and DataAnalyzer instances
        self._data_loader: dl.DataLoader = data_toolkit.data_loader
        self._data_plotter: dp.DataPlotter = data_toolkit.data_plotter
        self._data_analyzer: da.DataAnalyzer = data_toolkit.data_analyzer

        # Load the data when the DataManager is initialized
        self._data_loader.load_data()
        # Process the loaded data to prepare it for analysis
        self._data_loader.process_data()

        # Set the initial state of the DataManager to TRAIN
        self._state: dcm.DatasetType = dcm.DatasetType.TRAIN

    @property
    def state(self) -> dcm.DatasetType:
        return self._state

    @state.setter
    def state(self, value: dcm.DatasetType):
        self._state = value

    def plot_all_tacs(self):
        """
        Plots the TACs for all patients in the dataset.
        """
        if (not self._create_img) and (not self._create_video):
            print(f"[{self._state}] Don't create any images or videos as configuration settings.")
            return
        for single_study in self.all_studies:
            study_id: str = single_study.study_id
            num_frame: int = single_study.num_subfolders
            print(f"Plotting TACs for patient: {study_id} with {single_study.num_subfolders} frames.")
            for i_frame in range(num_frame):
                # Plot the TAC for each patient and frame
                self.plot_tac(study_id, i_frame)
                # Store the plotted TAC as a PNG file for further analysis
                self.store_tac_png(study_id, i_frame)
            # Store the plotted TACs for the patient as a video
            self.store_tac_video(study_id, num_frame)

    def plot_tac(self, patient_id: str, num_img: int):
        """
        Plots the TACs for a given patient ID.

        Args:
            patient_id (str): The ID of the patient whose TACs are to be plotted.
            num_img (int): The index of the image to plot.
        """
        # Get the patient image path for the specified patient ID and image index
        patient_img_path: str = self.get_subfolders(patient_id)[num_img]
        # Check if the patient image path exists before plotting
        if not self.path_exists(patient_img_path):
            raise cm.NoFolderFound(patient_img_path)
        # Plot the TAC for the specified patient image path
        self._data_plotter.plot_tac(patient_img_path, patient_id, num_img)

    def store_tac_png(self, patient_id: str, num_img: int):
        if not self._create_img:
            print("Don't create any images as configuration settings.")
            return
        # Store the plotted TAC for further analysis
        patient_path: str = self.get_path(patient_id)
        self._data_plotter.save_tac(patient_path, num_img)

    def store_tac_video(self, patient_id: str, num_frame: int):
        if not self._create_video:
            print("Don't create any videos as configuration settings.")
            return
        self._data_plotter.save_video(patient_id, num_frame, self._state)

    def path_exists(self, path: str) -> bool:
        """
        Checks if a given path exists.

        Args:
            path (str): The path to check.
        """
        return self._folder_manager.folder_exists(path)

    @property
    def _study_catalog(self) -> dcm.StudyCatalog:
        return self._data_loader.get_study_catalog(self._state)

    def get_subfolders(self, study_id: str) -> tuple[str, ...]:
        return self._study_catalog.get_abs_subfolders(study_id)

    def get_path(self, study_id: str) -> str:
        return self._study_catalog.get_path(study_id)

    @property
    def all_studies(self) -> tuple[dcm.Study, ...]:
        return self._study_catalog.studies
