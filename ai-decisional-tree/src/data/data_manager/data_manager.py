"""
@brief Coordinate dataset access, TAC creation, image export, and volume export.
"""

from typing import Any

import pandas as pd

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm
import src.data.data_analyzer as da
import src.data.data_loader as dl
import src.data.data_manager.exceptions as ex
import src.data.data_plotter as dp
import src.data.data_toolkit as dt
import src.volume_manager as vm


class DataManager:
    """
    @brief Coordinate dataset loading, TAC generation, plotting, and volume export.


    Manager responsible for orchestrating dataset loading, TAC creation, plotting,
    and export operations for both raw and filtered image states.

    This class acts as the main coordination layer between:
    - the data-loading pipeline,
    - the plotting utilities,
    - the analysis utilities,
    - and the configuration / filesystem helpers.

    Attributes:
        _data_toolkit (DataToolkit): Toolkit object containing the configured
            dependencies used by the manager.
        _folder_manager (FolderManager): Filesystem abstraction for folder access.
        _config_parser (ConfigParser): Accessor to dataset and export settings.
        _data_loader (DataLoader): Loader used to read dataset metadata and studies.
        _data_plotter (DataPlotter): Plotting helper for TAC generation and export.
        _data_analyzer (DataAnalyzer): Analyzer used for filtering/processing data.
        _state (DatasetType): Current dataset subset (e.g., train/val/test).
        _image_state (ImageState): Current image-processing mode (raw or filtered).

    """

    def __init__(
        self,
        data_toolkit: dt.DataToolkit,
    ):
        """
        @brief Connect the toolkit components, load the dataset, and select initial states.


        Initialize the data manager and wire it to the required toolkit components.

        Args:
            data_toolkit (DataToolkit): Preconfigured toolkit instance exposing
                the folder manager, config parser, loader, plotter, and analyzer.

        @param data_toolkit: Configured toolkit supplying data-processing components.
        """
        # Store in a variable data toolkit
        self._data_toolkit: dt.DataToolkit = data_toolkit

        # Initialize the base class with the provided folder manager and config parser
        self._folder_manager: cm.FolderManager = self._data_toolkit.folder_manager
        self._config_parser: cp.ConfigParser = self._data_toolkit.config_parser

        # Initialize the DataLoader, DataPlotter and DataAnalyzer instances
        self._data_loader: dl.DataLoader = self._data_toolkit.data_loader
        self._data_plotter: dp.DataPlotter = self._data_toolkit.data_plotter
        self._data_analyzer: da.DataAnalyzer = self._data_toolkit.data_analyzer

        # Define the Volume Manager to create the data for the 3D tac
        self._volume_manager: vm.VolumeManager = vm.VolumeManager()

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
        """
        @brief Get or select the active dataset split.

        Return the currently selected dataset split.
        @return: The dcm.DatasetType produced by this operation.
        """
        return self._state

    @state.setter
    def state(self, value: dcm.DatasetType):
        """
        @brief Get or select the active dataset split.


        Set the active dataset split.

        Args:
            value (DatasetType): Dataset type such as TRAIN, VAL, or TEST.

        @param value: Dataset split to activate.
        """
        self._state = value

    def _set_flags(self):
        """
        @brief Configure callbacks, output flags, and intensity ranges for each image state.

        Build the per-image-state toolkit configuration for raw and filtered data.

        Each image state stores:
        - the corresponding flag configuration,
        - the function used to generate TACs,
        - the function to save PNGs,
        - the function to save videos,
        - the display range for image intensities.
        """
        # RAW
        raw_flag: dcm.Flag = dcm.Flag(
            img=self._config_parser.save_img,
            video=self._config_parser.save_video,
        )
        raw_img_range: dcm.ImageRange = dcm.ImageRange(
            lim_inf=self._data_analyzer.br_w_inf, lim_sup=self._data_analyzer.br_w_sup
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
        flt_img_range: dcm.ImageRange = dcm.ImageRange(lim_inf=0, lim_sup=1)
        flt_img_state_tlk: dcm.ImageStateToolkit = dcm.ImageStateToolkit(
            flag=flt_flag,
            create_tac_fn=self.create_filter_tac,
            store_tac_png_fn=self.store_tac_filter_png,
            store_tac_video_fn=self.store_tac_filter_video,
            img_range=flt_img_range,
        )

        # Storing the image state toolkit for each image state
        self._IMG_STATE_TLK_DICT: dict[dcm.ImageState, dcm.ImageStateToolkit] = {
            dcm.ImageState.RAW: raw_img_state_tlk,
            dcm.ImageState.FILTER: flt_img_state_tlk,
        }

    @property
    def image_state_toolkit(self) -> dcm.ImageStateToolkit:
        """
        @brief Return callbacks and settings for the active image state.


        Return the toolkit configuration associated with the current image state.

        Raises:
            ImageStateToolkitNotFound: If no toolkit is defined for the active state.

        @return: The dcm.ImageStateToolkit produced by this operation.
        @throws ImageStateToolkitNotFound: If the operation encounters this error.
        """
        try:
            return self._IMG_STATE_TLK_DICT[self._image_state]
        except KeyError as err:
            raise ex.ImageStateToolkitNotFound(self._image_state) from err

    @property
    def flag(self) -> dcm.Flag:
        """
        @brief Return output flags for the active image state.

        Return the active output configuration for the current image state.
        @return: The dcm.Flag produced by this operation.
        """
        return self.image_state_toolkit.flag

    @property
    def img_range(self) -> dcm.ImageRange:
        """
        @brief Return display intensity bounds for the active image state.

        Return the valid intensity window for the active image state.
        @return: The dcm.ImageRange produced by this operation.
        """
        return self.image_state_toolkit.img_range

    @property
    def create_tac_fn(self) -> Any:
        """
        @brief Return the TAC creation callback for the active image state.

        Return the callback used to create a TAC for the active image state.
        @return: The Any produced by this operation.
        """
        return self.image_state_toolkit.create_tac_fn

    @property
    def store_tac_png_fn(self) -> Any:
        """
        @brief Return the PNG-saving callback for the active image state.

        Return the callback used to save a TAC image for the active state.
        @return: The Any produced by this operation.
        """
        return self.image_state_toolkit.store_tac_png_fn

    @property
    def store_tac_video_fn(self) -> Any:
        """
        @brief Return the video-saving callback for the active image state.

        Return the callback used to export a TAC video for the active state.
        @return: The Any produced by this operation.
        """
        return self.image_state_toolkit.store_tac_video_fn

    def check_flag(self) -> bool:
        """
        @brief Return whether both image and video outputs are disabled.


        Verify whether all media outputs are disabled by configuration.

        Returns:
            bool: True if image and video generation are both disabled; otherwise False.

        @return: The bool produced by this operation.
        """
        if self.flag.all_media_disabled():
            print(f"[{self._state}] Don't create any images or videos as configuration settings.")
            return True
        return False

    def _create_tacs_for_state(self, image_state: dcm.ImageState):
        """
        @brief Generate and export TAC outputs for all studies in the selected image state.

        Generate all TACs for a given image-processing state.

        This method sets the active image state, checks the output flags, iterates
        through all studies and all frames, creates TACs, saves PNGs, and exports
        a video if configured.

        Args:
            image_state (ImageState): Target state, such as RAW or FILTER.

        @param image_state: Image-processing state to activate.
        """
        self._image_state = image_state
        print(f"Image state is: {self._image_state.name}")
        # Check the flags if it is necessary to plot images or videos
        if self.check_flag():
            return
        # Looping in each single study
        for single_study in self.all_studies:
            study_id: str = single_study.study_id
            num_frame: int = single_study.num_subfolders
            print(f"[Images] TACs for patient: {study_id} with {num_frame} frames.")
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

    def create_volume_tacs(self):
        """
        @brief Build and save volume records for every study in the active split.
        """
        # Looping in each single study
        for single_study in self.all_studies:
            study_id: str = single_study.study_id
            num_frame: int = single_study.num_subfolders
            print(f"[Volume] TACs for patient: {study_id} with {single_study.num_subfolders} frames.")
            for i_frame in range(num_frame):
                # Concatenate the tacs to have the volume of the head\brain
                self.concatenate_tac(study_id, i_frame)
            # Store the 3D image into a single file
            self.store_volume_tac(study_id)

    def concatenate_tac(self, patient_id: str, num_img: int):
        """
        @brief Append one study frame's image and mask matrices to the pending volume.
        @param patient_id: Study identifier.
        @param num_img: Frame index within the study.
        """
        patient_img_path: str = self.get_patient_img_path(patient_id, num_img)
        # Load the matrices
        img_matrix, mask_matrix = self._data_plotter.load_matrices(patient_img_path)
        self._volume_manager.add_img(img_matrix)
        self._volume_manager.add_msk(mask_matrix)

    def store_volume_tac(self, patient_id: str):
        # Build the volume
        """
        @brief Build, save, and clear the pending patient volume.
        @param patient_id: Study identifier.
        """
        self._volume_manager.build()
        # Get the dataframe
        df: pd.DataFrame = self._volume_manager.records
        # Store the file in the pc
        self._data_loader.store_volume(df, patient_id, self._state)
        # Finally clean the object
        self._volume_manager.clean()

    def _reset_vars(self):
        """
        @brief Clear cached image-manager instances after processing a study.

        Clear cached image-manager instances after processing a study to avoid
        stale state and reduce memory retention.
        """
        self._data_toolkit.reset_img_manager_dict()

    def create_all_tacs(self):
        """
        @brief Generate TAC outputs for all studies using raw images.


        Generate TACs for all patients using the raw image state.

        This is the standard pipeline for unfiltered CT data.

        """
        self._create_tacs_for_state(dcm.ImageState.RAW)

    def create_all_tacs_filtered(self):
        """
        @brief Generate TAC outputs for all studies using filtered images.


        Generate TACs for all patients using the filtered image state.

        This method is intended for processed data after brain-windowing and
        filtering operations have been applied.

        """
        self._create_tacs_for_state(dcm.ImageState.FILTER)

    def get_patient_img_path(self, patient_id: str, num_img: int):
        """
        @brief Resolve a study frame index to its existing image directory.


        Resolve the path to the selected image for a given patient and frame index.

        Args:
            patient_id (str): Study identifier.
            num_img (int): Frame index within the study.

        Returns:
            str: Absolute or project-relative path to the image folder.

        Raises:
            NoFolderFound: If the target folder does not exist.

        @param patient_id: Study identifier.
        @param num_img: Frame index within the study.
        @return: The value produced by this operation.
        @throws NoFolderFound: If the operation encounters this error.
        """
        # Get the patient image path for the specified patient ID and image index
        patient_img_path: str = self.get_subfolders(patient_id)[num_img]
        # Check if the patient image path exists before plotting
        if not self.path_exists(patient_img_path):
            raise cm.NoFolderFound(patient_img_path)
        return patient_img_path

    def create_tac(self, patient_id: str, num_img: int):
        """
        @brief Plot the raw image and mask for one study frame.


        Plot a TAC for a given patient image frame using the raw data state.

        Args:
            patient_id (str): Identifier of the patient/study.
            num_img (int): Index of the source image frame.

        @param patient_id: Study identifier.
        @param num_img: Frame index within the study.
        """
        patient_img_path: str = self.get_patient_img_path(patient_id, num_img)
        # Load the matrices
        img_matrix, mask_matrix = self._data_plotter.load_matrices(patient_img_path)
        # Create the TAC for the specified patient image path
        self._data_plotter.create_tac(img_matrix, mask_matrix, patient_id, num_img, self.img_range)

    def store_tac_png(self, patient_id: str, num_img: int):
        """
        @brief Save the current raw TAC plot as a PNG file.


        Save the generated raw TAC plot as a PNG file.

        Args:
            patient_id (str): Identifier of the patient/study.
            num_img (int): Index of the plotted frame.

        @param patient_id: Study identifier.
        @param num_img: Frame index within the study.
        """
        # Store the plotted TAC for further analysis
        patient_path: str = self.get_path(patient_id)
        # Get the folders
        image_path, save_path = self._data_plotter.get_img_paths(patient_path, num_img)
        # Save the image
        self._data_plotter.save_tac(image_path, save_path)

    def store_tac_video(self, patient_id: str, num_frame: int):
        """
        @brief Save the raw TAC sequence as a patient video when enabled.


        Export the raw TAC sequence for a patient as a video.

        Args:
            patient_id (str): Identifier of the patient/study.
            num_frame (int): Number of frames to include in the exported video.

        @param patient_id: Study identifier.
        @param num_frame: Expected number of frames.
        """
        if self._check_video_flag():
            return
        # Video folder creation
        video_folder: str = self._data_plotter.get_video_folder(self._state)
        # Save the video
        self._data_plotter.save_video(patient_id, num_frame, video_folder)

    def _check_video_flag(self) -> bool:
        """
        @brief Check whether video output is disabled for the active image state.

        Check whether video export is enabled for the current image state.

        Returns:
            bool: True if video generation was disabled by configuration; otherwise False.

        @return: True when video creation is disabled; otherwise False.
        """
        if not self.flag.video:
            print("Don't create any videos as configuration settings.")
            return True
        return False

    def create_filter_tac(self, patient_id: str, num_img: int):
        """
        @brief Filter and plot one study frame using the filtered image state.


        Plot a TAC for the filtered image state of a patient frame.

        This method applies the configured filtering stage before generating the
        visualization.

        Args:
            patient_id (str): Identifier of the patient/study.
            num_img (int): Index of the source image frame.

        @param patient_id: Study identifier.
        @param num_img: Frame index within the study.
        """
        patient_img_raw_path: str = self.get_patient_img_path(patient_id, num_img)
        # Filter the img
        self._data_analyzer.filter_frame(patient_img_raw_path)
        # Load the matrices
        img_flt_matrix, mask_matrix = self._data_analyzer.load_filtered_matrices(patient_img_raw_path)
        # Create the TAC for the specified patient image path
        self._data_plotter.create_tac(img_flt_matrix, mask_matrix, patient_id, num_img, self.img_range)

    def store_tac_filter_png(self, patient_id: str, num_img: int):
        """
        @brief Save the current filtered TAC plot as a PNG file.


        Save the filtered TAC plot as a PNG file.

        Args:
            patient_id (str): Identifier of the patient/study.
            num_img (int): Index of the plotted frame.

        @param patient_id: Study identifier.
        @param num_img: Frame index within the study.
        """
        # Store the plotted TAC for further analysis
        patient_path: str = self.get_path(patient_id)
        # Get the folders
        image_flt_path, save_flt_path = self._data_plotter.get_img_flt_paths(patient_path, num_img)
        # Save the image
        self._data_plotter.save_tac(image_flt_path, save_flt_path)

    def store_tac_filter_video(self, patient_id: str, num_frame: int):
        """
        @brief Save the filtered TAC sequence as a patient video when enabled.


        Export the filtered TAC sequence for a patient as a video.

        Args:
            patient_id (str): Identifier of the patient/study.
            num_frame (int): Number of frames to include in the exported video.

        @param patient_id: Study identifier.
        @param num_frame: Expected number of frames.
        """
        if self._check_video_flag():
            return
        # Video folder creation
        video_flt_folder: str = self._data_plotter.get_video_flt_folder(self._state)
        # Save the video
        self._data_plotter.save_video(patient_id, num_frame, video_flt_folder)

    def path_exists(self, path: str) -> bool:
        """
        @brief Check whether a given filesystem path exists as a directory.


        Check whether a given filesystem path exists.

        Args:
            path (str): Directory or file path to validate.

        Returns:
            bool: True if the path exists; otherwise False.

        @param path: Filesystem path to inspect or process.
        @return: The bool produced by this operation.
        """
        return self._folder_manager.folder_exists(path)

    @property
    def _study_catalog(self) -> dcm.StudyCatalog:
        """
        @brief Return the study catalog associated with the active dataset split.
        @return: The catalog for the currently selected dataset split.
        """
        return self._data_loader.get_study_catalog(self._state)

    def get_subfolders(self, study_id: str) -> tuple[str, ...]:
        """
        @brief Return absolute frame-directory paths recorded for a study.


        Return the absolute subfolder paths for a study.

        Args:
            study_id (str): Identifier of the study.

        Returns:
            tuple[str, ...]: Ordered subfolder paths for the given study.

        @param study_id: Unique study identifier.
        @return: The tuple[str, ...] produced by this operation.
        """
        return self._study_catalog.get_abs_subfolders(study_id)

    def get_path(self, study_id: str) -> str:
        """
        @brief Return the recorded base filesystem path for a study.


        Return the base filesystem path for a study.

        Args:
            study_id (str): Identifier of the study.

        Returns:
            str: Base study path.

        @param study_id: Unique study identifier.
        @return: The str produced by this operation.
        """
        return self._study_catalog.get_path(study_id)

    @property
    def all_studies(self) -> tuple[dcm.Study, ...]:
        """
        @brief Return all studies in the active dataset split.

        Return all studies contained in the active dataset split.
        @return: The tuple[dcm.Study, ...] produced by this operation.
        """
        return self._study_catalog.studies

    def check_studies_catalog_lethality_balance(self):
        """
        @brief Check the balance of lethality values in the study catalog.
        @return: The bool produced by this operation.
        """
        for dataset_type, study_catalog in self._data_loader.get_all_study_catalog().items():
            lethality_percentage: float = study_catalog.get_lethality_percentage()
            print(f"[{dataset_type.name}] Lethality balance: {lethality_percentage}%")
