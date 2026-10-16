from typing import Any

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm
import src.data.data_loader as dl
import src.data.data_plotter as dp
import src.data.data_analyzer as da
import src.data.data_toolkit as dt
import src.data.data_manager.exceptions as ex


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
            data_toolkit: dt.DataToolkit,
    ):
        """
        Initializes the DataManager with instances of DataLoader, DataPlotter, and DataAnalyzer.

        Args:
            data_toolkit (DataToolkit): An instance of the DataToolkit class.
        """
        # Store in a variable data toolkit
        self._data_toolkit: dt.DataToolkit = data_toolkit

        # Initialize the base class with the provided folder manager and config parser
        self._folder_manager: cm.FolderManager = self._data_toolkit.folder_manager
        self._config_parser:  cp.ConfigParser = self._data_toolkit.config_parser

        # Initialize the DataLoader, DataPlotter, and DataAnalyzer instances
        self._data_loader: dl.DataLoader = self._data_toolkit.data_loader
        self._data_plotter: dp.DataPlotter = self._data_toolkit.data_plotter
        self._data_analyzer: da.DataAnalyzer = self._data_toolkit.data_analyzer

        # Get initial flags
        self._set_flags()

        # Load the data when the DataManager is initialized
        self._data_loader.load_data()
        # Process the loaded data to prepare it for analysis
        self._data_loader.process_data()

        # Set the initial state of the DataManager to TRAIN
        self._state: dcm.DatasetType = dcm.DatasetType.TRAIN
        # State of the image processing
        self._image_state: dcm.ImageState = dcm.ImageState.RAW

    @property
    def state(self) -> dcm.DatasetType:
        return self._state

    @state.setter
    def state(self, value: dcm.DatasetType):
        self._state = value

    def _set_flags(self):
        # RAW
        raw_flag: dcm.Flag = dcm.Flag(
            img=self._config_parser.save_img,
            video=self._config_parser.save_video,
        )
        raw_img_range: dcm.ImageRange = dcm.ImageRange(
            lim_inf=self._data_analyzer.br_w_inf,
            lim_sup=self._data_analyzer.br_w_sup
        )
        raw_img_state_tlk: dcm.ImageStateToolkit = dcm.ImageStateToolkit(
            flag=raw_flag,
            create_tac_fn=self.create_tac,
            store_tac_png_fn=self.store_tac_png,
            store_tac_video_fn=self.store_tac_video,
            img_range=raw_img_range,
        )
        # FILTERED
        flt_flag: dcm.Flag = dcm.Flag(
            img=self._config_parser.save_img_flt,
            video=self._config_parser.save_video_flt,
        )
        # The range is normalized
        flt_img_range: dcm.ImageRange = dcm.ImageRange(
            lim_inf=0,
            lim_sup=1
        )
        flt_img_state_tlk: dcm.ImageStateToolkit = dcm.ImageStateToolkit(
            flag=flt_flag,
            create_tac_fn=self.create_filter_tac,
            store_tac_png_fn=self.store_tac_filter_png,
            store_tac_video_fn=self.store_tac_filter_video,
            img_range=flt_img_range,
        )

        # Storing the image state toolkit for each image state
        self._IMG_STATE_TLK_DICT: dict[dcm.ImageState, dcm.ImageStateToolkit] = \
        {
            dcm.ImageState.RAW: raw_img_state_tlk,
            dcm.ImageState.FILTER: flt_img_state_tlk,
        }

    @property
    def image_state_toolkit(self) -> dcm.ImageStateToolkit:
        try:
            return self._IMG_STATE_TLK_DICT[self._image_state]
        except KeyError:
            raise ex.ImageStateToolkitNotFound(self._image_state)

    @property
    def flag(self) -> dcm.Flag:
        return self.image_state_toolkit.flag

    @property
    def img_range(self) -> dcm.ImageRange:
        return self.image_state_toolkit.img_range

    @property
    def create_tac_fn(self) -> Any:
        return self.image_state_toolkit.create_tac_fn

    @property
    def store_tac_png_fn(self) -> Any:
        return self.image_state_toolkit.store_tac_png_fn

    @property
    def store_tac_video_fn(self) -> Any:
        return self.image_state_toolkit.store_tac_video_fn

    def check_flag(self) -> bool:
        if self.flag.all_media_disabled():
            print(f"[{self._state}] Don't create any images or videos as configuration settings.")
            return True
        return False

    def _create_tacs_for_state(self, image_state: dcm.ImageState):
        self._image_state = image_state
        print(f"Image state is: {self._image_state.name}")
        # Check the flags if it is necessary to plot images or videos
        if self.check_flag():
            return
        # Looping in each single study
        for single_study in self.all_studies:
            study_id: str = single_study.study_id
            num_frame: int = single_study.num_subfolders
            print(f"Plotting TACs for patient: {study_id} with {single_study.num_subfolders} frames.")
            for i_frame in range(num_frame):
                if not self.flag.img:
                    print("Don't create any images as configuration settings.")
                    return
                # Plot the TAC for each patient and frame
                self.create_tac_fn(study_id, i_frame)
                # Store the plotted TAC as a PNG file for further analysis
                self.store_tac_png_fn(study_id, i_frame)
            # Store the plotted TACs for the patient as a video
            self.store_tac_video_fn(study_id, num_frame)
            # Reset some variables
            self._reset_vars()

    def _reset_vars(self):
        self._data_toolkit.reset_img_manager_dict()

    def create_all_tacs(self):
        """
        Plots the TACs for all patients in the dataset.
        """
        self._create_tacs_for_state(dcm.ImageState.RAW)

    def create_all_tacs_filtered(self):
        """
        Plots the TACs filtered for all patients in the dataset.
        """
        self._create_tacs_for_state(dcm.ImageState.FILTER)

    def get_patient_img_path(self, patient_id: str, num_img: int):
        # Get the patient image path for the specified patient ID and image index
        patient_img_path: str = self.get_subfolders(patient_id)[num_img]
        # Check if the patient image path exists before plotting
        if not self.path_exists(patient_img_path):
            raise cm.NoFolderFound(patient_img_path)
        return patient_img_path

    def create_tac(self, patient_id: str, num_img: int):
        """
        Plots the TACs for a given patient ID.

        Args:
            patient_id (str): The ID of the patient whose TACs are to be plotted.
            num_img (int): The index of the image to plot.
        """
        patient_img_path: str = self.get_patient_img_path(patient_id, num_img)
        # Load the matrices
        img_matrix, mask_matrix = self._data_plotter.load_matrices(patient_img_path)
        # Create the TAC for the specified patient image path
        self._data_plotter.create_tac(img_matrix, mask_matrix, patient_id, num_img, self.img_range)

    def store_tac_png(self, patient_id: str, num_img: int):
        # Store the plotted TAC for further analysis
        patient_path: str = self.get_path(patient_id)
        # Get the folders
        image_path, save_path = self._data_plotter.get_img_paths(patient_path, num_img)
        # Save the image
        self._data_plotter.save_tac(image_path, save_path)

    def store_tac_video(self, patient_id: str, num_frame: int):
        if self._check_video_flag():
            return
        # Video folder creation
        video_folder: str = self._data_plotter.get_video_folder(self._state)
        # Save the video
        self._data_plotter.save_video(patient_id, num_frame, video_folder)

    def _check_video_flag(self) -> bool:
        if not self.flag.video:
            print("Don't create any videos as configuration settings.")
            return True
        return False

    def create_filter_tac(self, patient_id: str, num_img: int):
        """
        Plots the filtered TACs for a given patient ID.

        Args:
            patient_id (str): The ID of the patient whose TACs are to be plotted.
            num_img (int): The index of the image to plot.
        """
        patient_img_raw_path: str = self.get_patient_img_path(patient_id, num_img)
        # Filter the img
        self._data_analyzer.filter_frame(patient_img_raw_path)
        # Load the matrices
        img_flt_matrix, mask_matrix = self._data_analyzer.load_filtered_matrices(patient_img_raw_path)
        # Create the TAC for the specified patient image path
        self._data_plotter.create_tac(img_flt_matrix, mask_matrix, patient_id, num_img, self.img_range)

    def store_tac_filter_png(self, patient_id: str, num_img: int):
        # Store the plotted TAC for further analysis
        patient_path: str = self.get_path(patient_id)
        # Get the folders
        image_flt_path, save_flt_path = self._data_plotter.get_img_flt_paths(patient_path, num_img)
        # Save the image
        self._data_plotter.save_tac(image_flt_path, save_flt_path)

    def store_tac_filter_video(self, patient_id: str, num_frame: int):
        if self._check_video_flag():
            return
        # Video folder creation
        video_flt_folder: str = self._data_plotter.get_video_flt_folder(self._state)
        # Save the video
        self._data_plotter.save_video(patient_id, num_frame, video_flt_folder)

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
