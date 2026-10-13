import src.data.common as cm
import src.data.data_loader as dl
import src.data.data_plotter as dp
import src.data.data_analyzer as da


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
            data_loader: dl.DataLoader,
            data_plotter: dp.DataPlotter,
            data_analyzer: da.DataAnalyzer
    ):
        """
        Initializes the DataManager with instances of DataLoader, DataPlotter, and DataAnalyzer.

        Args:
            data_loader (DataLoader): An instance of the DataLoader class.
            data_plotter (DataPlotter): An instance of the DataPlotter class.
            data_analyzer (DataAnalyzer): An instance of the DataAnalyzer class.
        """
        # Initialize the DataLoader, DataPlotter, and DataAnalyzer instances
        self._data_loader: dl.DataLoader = data_loader
        self._data_plotter: dp.DataPlotter = data_plotter
        self._data_analyzer: da.DataAnalyzer = data_analyzer

        # Load the data when the DataManager is initialized
        self._data_loader.load_data()
        # Process the loaded data to prepare it for analysis
        self._data_loader.process_data()

        # Set the initial state of the DataManager to TRAIN
        self._state: cm.DatasetType = cm.DatasetType.TRAIN

    @property
    def state(self) -> cm.DatasetType:
        return self._state

    @state.setter
    def state(self, value: cm.DatasetType):
        self._state = value

    def plot_all_tacs(self):
        """
        Plots the TACs for all patients in the dataset.
        """
        for single_study in self.all_studies:
            self.plot_tac(single_study.study_id)

    def plot_tac(self, patient_id: str):
        """
        Plots the TACs for a given patient ID.

        Args:
            patient_id (str): The ID of the patient whose TACs are to be plotted.
        """
        patient_img_path: str = self.get_subfolders(patient_id)[0]
        self._data_plotter.plot_tac(patient_img_path)

    @property
    def _study_catalog(self) -> cm.StudyCatalog:
        return self._data_loader.get_study_catalog(self._state)

    def get_subfolders(self, dataset_name: str) -> tuple[str, ...]:
        return self._study_catalog.get_subfolders(dataset_name)

    @property
    def all_studies(self) -> tuple[cm.Study, ...]:
        return self._study_catalog.studies
