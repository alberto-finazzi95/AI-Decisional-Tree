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

    def load_matrices(self, patient_img_path: str) -> tuple[np.ndarray, np.ndarray]:
        # Compose the paths for the image and mask files
        img_path: str = self.compose_path(patient_img_path, ds.ImageFileType.IMG)
        mask_path: str = self.compose_path(patient_img_path, ds.ImageFileType.MASK)

        # Load the image and mask data
        img_matrix: np.ndarray = self.load_img(img_path)
        mask_matrix: np.ndarray = self.load_img(mask_path)

        return img_matrix, mask_matrix

    def plot_tac(self, patient_img_path: str, patient_id: str, num_img: int):
        # Load the image and mask data
        img_matrix, mask_matrix = self.load_matrices(patient_img_path)

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
    ):
        # Graphic 1: Native Brain CT (in grayscale, optimized for the brain)
        # We use vmin and vmax for an initial visual windowing (e.g., between 0 and 80 Hounsfield Units)
        ax: plt.Axes = self._axes[ax_index]
        image: plt.AxesImage = ax.imshow(img_matrix, cmap='gray', vmin=0, vmax=80)
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

    @staticmethod
    def load_img(img_path: str) -> np.ndarray:
        with np.load(img_path) as img_data:
            # Extract the image matrix from the loaded npz file
            img_key: str = next(iter(img_data.keys()))
            return img_data[img_key]

    def save_tac(
            self,
            patient_path: str,
            num_img: int):
        """
        Saves the current figure (TAC) to the specified path.

        Args:
            patient_path (str): The path of the patient.
            num_img (int): The index of the image.
        """
        image_path: str = self.compose_path(patient_path, cm.FolderName.IMAGE)
        save_path: str = self.compose_path(
            image_path,
            f"tac_{num_img}.png"
        )
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

    def _create_not_existing_folder(self, folder_path: str):
        if not self.path_exists(folder_path):
            print(f"Path '{folder_path}' does not exist. Creating...")
            self.create_folder(folder_path)

    def save_video(self, patient_id: str, num_frame: int, model_phase: dcm.DatasetType):
        # Video folder creation
        video_folder: str = self._get_video_folder(model_phase)
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

    def _get_video_folder(self, model_phase: dcm.DatasetType) -> str:
        return self.compose_path(
            self._dataset_output_folder_name,
            model_phase,
            cm.FolderName.VIDEO,
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
