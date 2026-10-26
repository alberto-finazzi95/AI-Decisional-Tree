import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clr
import imageio as iio
import imageio.v3 as iio3

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm

import src.data.data_plotter.exceptions as ex
import src.data.data_plotter.data_structures as ds


class DataPlotter(dcm.BaseData):
    TICK_LABELS: list[str] = ['0: Healthy / Background', '1: Core Ischemic', '2: Penumbra']
    IMG_TITLE: str = "TC Unenhanced Brain"
    MASK_TITLE: str = "Clinical Segmentation Mask (Ground Truth)"

    def __init__(
            self,
            folder_manager: cm.FolderManager,
            config_parser: cp.ConfigParser,
            os_manager: cm.OsManager | None = None,
    ):
        super().__init__(folder_manager, config_parser, os_manager)
        self._frame_for_video: list = []
        self._create_figure()

    @property
    def fig(self) -> plt.Figure:
        return self._fig

    def clean_frame_for_video(self):
        self._frame_for_video.clear()

    def _create_figure(self) -> None:
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
        self.plot_mask(
            1,
            mask_matrix,
            self.MASK_TITLE
        )

        self._fig.tight_layout()
        self._clear_axes()

    def _clear_axes(self):
        for ax in self._axes:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_axis_off()

    def _close_figure_if_needed(self):
        if not plt.fignum_exists(self._fig.number):
            self._create_figure()
            return

        self._fig.clear()
        self._axes = self._fig.subplots(1, 2)
        self._clear_axes()

    @staticmethod
    def set_fig_title(patient_id: str, num_img: int) -> str:
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
        ax: plt.Axes = self._axes[ax_index]
        image: plt.AxesImage = ax.imshow(img_matrix, cmap='gray', vmin=img_range.lim_inf, vmax=img_range.lim_sup)
        ax.set_title(title)
        ax.figure.colorbar(image, ax=ax, label="Density (HU)", fraction=0.046, pad=0.04)

    def plot_mask(
            self,
            ax_index: int,
            mask_matrix: np.ndarray,
            title: str
    ):
        ax: plt.Axes = self._axes[ax_index]
        # Graphic 2: Clinical Segmentation Mask (Ground Truth)
        # We define a discrete colormap: 0=Black (Healthy), 1=Red (Core), 2=Yellow (Penumbra)
        colors: list[str] = ['black', 'red', 'yellow']
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
        return self.compose_path(patient_path, cm.FolderName.IMAGE)

    def _get_save_path(self, image_path: str, num_img: int) -> str:
        return self.compose_path(image_path, f"tac_{num_img}.png")

    def get_img_paths(self, patient_path: str, num_img: int) -> tuple[str, str]:
        image_path: str = self._get_img_path(patient_path)
        save_path: str = self._get_save_path(image_path, num_img)
        return image_path, save_path

    def _get_img_flt_path(self, patient_path: str) -> str:
        return self.compose_path(patient_path, cm.FolderName.IMAGE_FLT)

    def _get_save_flt_path(self, image_path: str, num_img: int) -> str:
        return self.compose_path(image_path, f"tac_filtered_{num_img}.png")

    def get_img_flt_paths(self, patient_path: str, num_img: int) -> tuple[str, str]:
        image_flt_path: str = self._get_img_flt_path(patient_path)
        save_flt_path: str = self._get_save_flt_path(image_flt_path, num_img)
        return image_flt_path, save_flt_path

    def save_tac(self, image_path: str, save_path: str):
        """
        Saves the current figure (TAC) to the specified path.

        Args:
            image_path (str): The path of the patient images storage.
            save_path (str): The path of the patient videos storage.
        """
        # Store the path of the saved TAC for video creation
        self._frame_for_video.append(save_path)
        # Ensure the image path exists; if not, create it
        self._create_not_existing_folder(image_path)
        # Save the figure if it doesn't already exist
        self.save_figure_tac(save_path)

    def save_figure_tac(self, save_path: str):
        if self.file_exists(save_path):
            print(f"TAC already exists at {save_path}. Skipping save.")
            return
        self._fig.savefig(save_path)
        print(f"TAC saved to {save_path}")

    def save_video(self, patient_id: str, num_frame: int, video_folder: str):
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
        num_frame_read: int = len(self._frame_for_video)
        if num_frame_read != num_frame_expected:
            raise ex.NotEnoughPngFiles(patient_id, num_frame_read, num_frame_expected)

    def get_video_folder(self, model_phase: dcm.DatasetType) -> str:
        return self.compose_path(
            self._dataset_output_folder_name,
            model_phase,
            cm.FolderName.VIDEO,
        )

    def get_video_flt_folder(self, model_phase: dcm.DatasetType) -> str:
        return self.compose_path(
            self._dataset_output_folder_name,
            model_phase,
            cm.FolderName.VIDEO_FLT,
        )

    def _get_video_path(self, patient_id: str, video_folder: str) -> str:
        file_name: str = f"video_{patient_id}.mp4"
        return self.compose_path(video_folder, file_name)

    @staticmethod
    def get_video_writer(video_path: str):
        video_fps: int = ds.VideoInfo.fps
        video_mode: str = ds.VideoInfo.mode
        video_format: str = ds.VideoInfo.format
        return iio.get_writer(video_path, fps=video_fps, mode=video_mode, format=video_format)
