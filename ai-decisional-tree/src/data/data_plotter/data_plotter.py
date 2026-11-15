"""
@brief Create and save image/mask TAC plots and patient videos.
"""
import imageio as iio
import imageio.v3 as iio3
import matplotlib.colors as clr
import matplotlib.pyplot as plt
import numpy as np

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm
import src.data.data_plotter.data_structures as ds
import src.data.data_plotter.exceptions as ex


class DataPlotter(dcm.BaseData):
    """
    @brief Render image/mask TACs and save PNG and video outputs.
    """
    TICK_LABELS: list[str] = ["0: Healthy / Background", "1: Core Ischemic", "2: Penumbra"]
    IMG_TITLE: str = "TC Unenhanced Brain"
    MASK_TITLE: str = "Clinical Segmentation Mask (Ground Truth)"

    def __init__(
        self,
        folder_manager: cm.FolderManager,
        config_parser: cp.ConfigParser,
        os_manager: cm.OsManager | None = None,
    ):
        """
        @brief Initialize shared data paths and create the TAC plotting figure.
        @param folder_manager: Folder manager used for filesystem operations.
        @param config_parser: Parser providing dataset and output settings.
        @param os_manager: Optional filesystem-operation implementation.
        """
        super().__init__(folder_manager, config_parser, os_manager)
        self._frame_for_video: list = []
        self._create_figure()

    @property
    def fig(self) -> plt.Figure:
        """
        @brief Return the Matplotlib figure used for TAC rendering.
        @return: The plt.Figure produced by this operation.
        """
        return self._fig

    def clean_frame_for_video(self):
        """
        @brief Discard the collected PNG paths for the next video.
        """
        self._frame_for_video.clear()

    def _create_figure(self) -> None:
        """
        @brief Create the two-panel Matplotlib figure used for image and mask plots.
        """
        self._fig, self._axes = plt.subplots(1, 2, figsize=(12, 6))
        self._clear_axes()

    def create_tac(
        self,
        img_matrix: np.ndarray,
        mask_matrix: np.ndarray,
        patient_id: str,
        num_img: int,
        img_range: dcm.ImageRange,
    ):
        # Closing a pyplot window unregisters its figure; create a new one if needed.
        """
        @brief Render an image matrix and its segmentation mask in the current figure.
        @param img_matrix: Image matrix for the operation.
        @param mask_matrix: Segmentation-mask matrix.
        @param patient_id: Study identifier.
        @param num_img: Frame index within the study.
        @param img_range: Intensity range used to display the image.
        """
        self._close_figure_if_needed()

        # Set the figure title and create subplots for the image and mask
        fig_title: str = self.set_fig_title(patient_id, num_img)
        self._fig.suptitle(fig_title)

        # Plot the image
        self.plot_img(
            0,
            img_matrix,
            self.IMG_TITLE,
            img_range,
        )
        # Plot the mask
        self.plot_mask(1, mask_matrix, self.MASK_TITLE)

        self._fig.tight_layout()
        self._clear_axes()

    def _clear_axes(self):
        """
        @brief Hide ticks and axes decorations on both plot panels.
        """
        for ax in self._axes:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_axis_off()

    def _close_figure_if_needed(self):
        """
        @brief Recreate a closed figure or clear the current figure for reuse.
        """
        if not plt.fignum_exists(self._fig.number):
            self._create_figure()
            return

        self._fig.clear()
        self._axes = self._fig.subplots(1, 2)
        self._clear_axes()

    @staticmethod
    def set_fig_title(patient_id: str, num_img: int) -> str:
        """
        @brief Format the figure title from the study ID and frame index.
        @param patient_id: Study identifier.
        @param num_img: Frame index within the study.
        @return: The str produced by this operation.
        """
        return f"ID: {patient_id}\nFrame: {num_img}"

    def plot_img(
        self,
        ax_index: int,
        img_matrix: np.ndarray,
        title: str,
        img_range: dcm.ImageRange,
    ):
        # Graphic 1: Native Brain CT (in grayscale, optimized for the brain)
        # We use vmin and vmax for an initial visual windowing (e.g., between 0 and 80 Hounsfield Units)
        """
        @brief Draw an image matrix using the supplied intensity range and title.
        @param ax_index: Index of the plot axes to use.
        @param img_matrix: Image matrix for the operation.
        @param title: Title displayed for the plot.
        @param img_range: Intensity range used to display the image.
        """
        ax: plt.Axes = self._axes[ax_index]
        image: plt.AxesImage = ax.imshow(img_matrix, cmap="gray", vmin=img_range.lim_inf, vmax=img_range.lim_sup)
        ax.set_title(title)
        ax.figure.colorbar(image, ax=ax, label="Density (HU)", fraction=0.046, pad=0.04)

    def plot_mask(self, ax_index: int, mask_matrix: np.ndarray, title: str):
        """
        @brief Draw a segmentation mask using the configured class colors.
        @param ax_index: Index of the plot axes to use.
        @param mask_matrix: Segmentation-mask matrix.
        @param title: Title displayed for the plot.
        """
        ax: plt.Axes = self._axes[ax_index]
        # Graphic 2: Clinical Segmentation Mask (Ground Truth)
        # We define a discrete colormap: 0=Black (Healthy), 1=Red (Core), 2=Yellow (Penumbra)
        colors: list[str] = ["black", "red", "yellow"]
        cmap_mask: clr.ListedColormap = clr.ListedColormap(colors)

        # Setting vmin=0 and vmax=2 to map exactly the 3 classes
        im: plt.AxesImage = ax.imshow(mask_matrix, cmap=cmap_mask, vmin=0, vmax=2)
        ax.set_title(title)

        # Configuring the colorbar for the mask colormap
        cbar: plt.Colorbar = self._fig.colorbar(
            im,
            ax=ax,
            ticks=[0, 1, 2],
            fraction=0.046,
            pad=0.04,
        )
        cbar.ax.set_yticklabels(self.TICK_LABELS)

    def _get_img_path(self, patient_path: str) -> str:
        """
        @brief Compose the raw image-output directory for a patient.
        @param patient_path: Patient directory used as the output parent.
        @return: The composed raw image directory path.
        """
        return self.compose_path(patient_path, cm.FolderName.IMAGE)

    def _get_save_path(self, image_path: str, num_img: int) -> str:
        """
        @brief Compose the PNG path for one raw TAC frame.
        @param image_path: Raw image-output directory.
        @param num_img: Frame index used in the file name.
        @return: The composed PNG file path.
        """
        return self.compose_path(image_path, f"tac_{num_img}.png")

    def get_img_paths(self, patient_path: str, num_img: int) -> tuple[str, str]:
        """
        @brief Return the raw TAC output directory and frame PNG path.
        @param patient_path: Directory containing the patient image and mask files.
        @param num_img: Frame index within the study.
        @return: The tuple[str, str] produced by this operation.
        """
        image_path: str = self._get_img_path(patient_path)
        save_path: str = self._get_save_path(image_path, num_img)
        return image_path, save_path

    def _get_img_flt_path(self, patient_path: str) -> str:
        """
        @brief Compose the filtered image-output directory for a patient.
        @param patient_path: Patient directory used as the output parent.
        @return: The composed filtered image directory path.
        """
        return self.compose_path(patient_path, cm.FolderName.IMAGE_FLT)

    def _get_save_flt_path(self, image_path: str, num_img: int) -> str:
        """
        @brief Compose the PNG path for one filtered TAC frame.
        @param image_path: Filtered image-output directory.
        @param num_img: Frame index used in the file name.
        @return: The composed PNG file path.
        """
        return self.compose_path(image_path, f"tac_filtered_{num_img}.png")

    def get_img_flt_paths(self, patient_path: str, num_img: int) -> tuple[str, str]:
        """
        @brief Return the filtered TAC output directory and frame PNG path.
        @param patient_path: Directory containing the patient image and mask files.
        @param num_img: Frame index within the study.
        @return: The tuple[str, str] produced by this operation.
        """
        image_flt_path: str = self._get_img_flt_path(patient_path)
        save_flt_path: str = self._get_save_flt_path(image_flt_path, num_img)
        return image_flt_path, save_flt_path

    def save_tac(self, image_path: str, save_path: str):
        """
        @brief Queue and save the current TAC figure as a PNG when needed.


        Saves the current figure (TAC) to the specified path.

        Args:
            image_path (str): The path of the patient images storage.
            save_path (str): The path of the patient videos storage.

        @param image_path: Directory containing or identifying image output.
        @param save_path: Destination path for the output file.
        """
        # Store the path of the saved TAC for video creation
        self._frame_for_video.append(save_path)
        # Ensure the image path exists; if not, create it
        self._create_not_existing_folder(image_path)
        # Save the figure if it doesn't already exist
        self.save_figure_tac(save_path)

    def save_figure_tac(self, save_path: str):
        """
        @brief Save the current figure unless the target file already exists.
        @param save_path: Destination path for the output file.
        """
        if self.file_exists(save_path):
            print(f"TAC already exists at {save_path}. Skipping save.")
            return
        self._fig.savefig(save_path)
        print(f"TAC saved to {save_path}")

    def save_video(self, patient_id: str, num_frame: int, video_folder: str):
        """
        @brief Write collected PNG frames to a patient video and clear the frame queue.
        @param patient_id: Study identifier.
        @param num_frame: Expected number of frames.
        @param video_folder: Directory for the output video.
        """
        self._create_not_existing_folder(video_folder)
        # Single video path
        video_path: str = self._get_video_path(patient_id, video_folder)
        if self.file_exists(video_path):
            print(f"TAC video already exists at {video_path}. Skipping save.")
            # Reset the frames
            self.clean_frame_for_video()
            return
        # Check if the list self._frame_for_video has all the png files
        self._check_num_frame(patient_id, num_frame)
        with self.get_video_writer(video_path) as writer:
            for png in self._frame_for_video:
                writer.append_data(iio3.imread(png))
        print(f"Video created at {video_path}")
        # Reset the frames
        self.clean_frame_for_video()

    def _check_num_frame(self, patient_id: str, num_frame_expected: int):
        """
        @brief Ensure the queued PNG count matches the expected frame count.
        @param patient_id: Study identifier used in any raised error.
        @param num_frame_expected: Number of frames expected for the study.
        @throws NotEnoughPngFiles: If the queued and expected counts differ.
        """
        num_frame_read: int = len(self._frame_for_video)
        if num_frame_read != num_frame_expected:
            raise ex.NotEnoughPngFiles(patient_id, num_frame_read, num_frame_expected)

    def get_video_folder(self, model_phase: dcm.DatasetType) -> str:
        """
        @brief Return the raw video output directory for a dataset split.
        @param model_phase: Dataset split for the output.
        @return: The str produced by this operation.
        """
        return self.compose_path(
            self._dataset_output_folder_name,
            model_phase,
            cm.FolderName.VIDEO,
        )

    def get_video_flt_folder(self, model_phase: dcm.DatasetType) -> str:
        """
        @brief Return the filtered video output directory for a dataset split.
        @param model_phase: Dataset split for the output.
        @return: The str produced by this operation.
        """
        return self.compose_path(
            self._dataset_output_folder_name,
            model_phase,
            cm.FolderName.VIDEO_FLT,
        )

    def _get_video_path(self, patient_id: str, video_folder: str) -> str:
        """
        @brief Compose the MP4 output path for a patient's TAC video.
        @param patient_id: Study identifier used in the video file name.
        @param video_folder: Directory where the video is stored.
        @return: The composed MP4 file path.
        """
        file_name: str = f"video_{patient_id}.mp4"
        return self.compose_path(video_folder, file_name)

    @staticmethod
    def get_video_writer(video_path: str):
        """
        @brief Create an imageio video writer using project encoding settings.
        @param video_path: Path for the output video.
        @return: The value produced by this operation.
        """
        video_fps: int = ds.VideoInfo.fps
        video_mode: str = ds.VideoInfo.mode
        video_format: str = ds.VideoInfo.format
        return iio.get_writer(video_path, fps=video_fps, mode=video_mode, format=video_format)
