import unittest
from unittest.mock import Mock, call, patch

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import src.common as cm
import src.data.common as dcm
import src.data.data_plotter.data_plotter as dp
import src.data.data_plotter.exceptions as ex

import tests.helper as h


class DataPlotterTests(unittest.TestCase):
    """Tests plot rendering, output paths, and PNG/video persistence."""

    FILE_NO_EXIST: str = "_create_not_existing_folder"
    FILE_EXISTS: str = "file_exists"
    SAVE_FIGURE_METHOD: str = "savefig"
    VIDEO_WRITER_METHOD: str = "get_video_writer"
    STUDY_ID: str = "study"
    STUDY_ID_1: str = "study-1"
    IMAGE_FOLDER: str = "images"
    TAC_IMAGE_PATH: str = "images/tac_0.png"
    VIDEO_FOLDER: str = "videos"
    FRAME_0_PATH: str = "frame-0.png"
    FRAME_1_PATH: str = "frame-1.png"
    FRAME_0_IMAGE: str = "img0"
    FRAME_1_IMAGE: str = "img1"

    def setUp(self):
        _, self.folder_manager, config_parser = h.make_data_dependencies()
        self.plotter: dp.DataPlotter = dp.DataPlotter(self.folder_manager, config_parser)

    def tearDown(self):
        plt.close(self.plotter.fig)

    def test_title_and_raw_and_filtered_output_paths(self):
        """Check figure titles and raw or filtered output path composition."""
        self.assertEqual(dp.DataPlotter.set_fig_title(self.STUDY_ID_1, 3), "ID: study-1\nFrame: 3")
        image_path: str = self.plotter.compose_path(self.STUDY_ID, cm.FolderName.IMAGE)
        filtered_image_path: str = self.plotter.compose_path(self.STUDY_ID, cm.FolderName.IMAGE_FLT)
        self.assertEqual(
            self.plotter.get_img_paths(self.STUDY_ID, 2),
            (image_path, self.plotter.compose_path(image_path, "tac_2.png")),
        )
        self.assertEqual(
            self.plotter.get_img_flt_paths(self.STUDY_ID, 2),
            (filtered_image_path, self.plotter.compose_path(filtered_image_path, "tac_filtered_2.png")),
        )

    def test_create_tac_renders_image_and_mask_with_expected_titles(self):
        """Verify image and mask plots use the expected titles and intensity ranges."""
        self.plotter.create_tac(
            np.ones((3, 3)),
            np.array([[0, 1, 2]]),
            self.STUDY_ID_1,
            4,
            dcm.ImageRange(lim_inf=0, lim_sup=80),
        )

        self.assertEqual(self.plotter.fig._suptitle.get_text(), f"ID: {self.STUDY_ID_1}\nFrame: 4")
        self.assertEqual(self.plotter.fig.axes[0].get_title(), self.plotter.IMG_TITLE)
        self.assertEqual(self.plotter.fig.axes[1].get_title(), self.plotter.MASK_TITLE)
        self.assertEqual(self.plotter.fig.axes[0].images[0].get_clim(), (0, 80))
        self.assertEqual(self.plotter.fig.axes[1].images[0].get_clim(), (0, 2))

    def test_create_tac_recreates_closed_figure(self):
        """Ensure plotting recreates the Matplotlib figure after it has been closed."""
        old_figure = self.plotter.fig
        plt.close(old_figure)

        self.plotter.create_tac(
            np.zeros((2, 2)),
            np.zeros((2, 2)),
            self.STUDY_ID,
            0,
            dcm.ImageRange(lim_inf=0, lim_sup=1),
        )

        self.assertIsNot(self.plotter.fig, old_figure)
        self.assertTrue(plt.fignum_exists(self.plotter.fig.number))

    def test_save_tac_creates_parent_and_queues_frame_path(self):
        """Check saving a new TAC creates its folder, writes the figure, and queues it."""
        with patch.object(self.plotter, self.FILE_NO_EXIST) as create_folder:
            with patch.object(self.plotter, self.FILE_EXISTS, return_value=False):
                with patch.object(self.plotter.fig, self.SAVE_FIGURE_METHOD) as savefig:
                    self.plotter.save_tac(self.IMAGE_FOLDER, self.TAC_IMAGE_PATH)

        create_folder.assert_called_once_with(self.IMAGE_FOLDER)
        savefig.assert_called_once_with(self.TAC_IMAGE_PATH)
        self.assertEqual(self.plotter._frame_for_video, [self.TAC_IMAGE_PATH])

    def test_save_tac_skips_existing_png_but_queues_it(self):
        """Verify an existing TAC image is not rewritten but remains queued for video."""
        with patch.object(self.plotter, self.FILE_NO_EXIST):
            with patch.object(self.plotter, self.FILE_EXISTS, return_value=True):
                with patch.object(self.plotter.fig, self.SAVE_FIGURE_METHOD) as savefig:
                    self.plotter.save_tac(self.IMAGE_FOLDER, self.TAC_IMAGE_PATH)

        savefig.assert_not_called()
        self.assertEqual(self.plotter._frame_for_video, [self.TAC_IMAGE_PATH])

    def test_video_requires_exact_frame_count_and_preserves_queue_on_mismatch(self):
        """Ensure a mismatched frame count raises an error without clearing the queue."""
        self.plotter._frame_for_video.extend([self.FRAME_0_PATH])
        with self.assertRaisesRegex(ex.NotEnoughPngFiles, self.STUDY_ID):
            self.plotter._check_num_frame(self.STUDY_ID, 2)
        self.assertEqual(self.plotter._frame_for_video, [self.FRAME_0_PATH])

    def test_save_video_reads_frames_writes_video_and_clears_queue(self):
        """Check queued images are read, appended to the video, then removed from the queue."""
        self.plotter._frame_for_video.extend([self.FRAME_0_PATH, self.FRAME_1_PATH])
        writer = Mock()
        writer.__enter__ = Mock(return_value=writer)
        writer.__exit__ = Mock(return_value=False)
        with patch.object(self.plotter, self.FILE_NO_EXIST) as create_folder:
            with patch.object(self.plotter, self.FILE_EXISTS, return_value=False):
                with patch.object(dp.DataPlotter, self.VIDEO_WRITER_METHOD, return_value=writer) as get_writer:
                    with patch.object(dp.iio3, "imread", side_effect=[self.FRAME_0_IMAGE, self.FRAME_1_IMAGE]) as read:
                        self.plotter.save_video(self.STUDY_ID, 2, self.VIDEO_FOLDER)

        create_folder.assert_called_once_with(self.VIDEO_FOLDER)
        get_writer.assert_called_once_with(self.plotter._get_video_path(self.STUDY_ID, self.VIDEO_FOLDER))
        self.assertEqual(read.call_args_list, [call(self.FRAME_0_PATH), call(self.FRAME_1_PATH)])
        self.assertEqual(writer.append_data.call_args_list, [call(self.FRAME_0_IMAGE), call(self.FRAME_1_IMAGE)])
        writer.__exit__.assert_called_once()
        self.assertEqual(self.plotter._frame_for_video, [])

    def test_existing_video_skips_writing_and_clears_queue(self):
        """Verify an existing video is not rewritten and queued frame paths are cleared."""
        self.plotter._frame_for_video.append("frame.png")
        with patch.object(self.plotter, self.FILE_NO_EXIST):
            with patch.object(self.plotter, self.FILE_EXISTS, return_value=True):
                with patch.object(dp.DataPlotter, self.VIDEO_WRITER_METHOD) as get_writer:
                    self.plotter.save_video(self.STUDY_ID, 1, self.VIDEO_FOLDER)

        get_writer.assert_not_called()
        self.assertEqual(self.plotter._frame_for_video, [])

    def test_clean_frame_queue_discards_all_pending_frames(self):
        """Ensure frame cleanup removes every pending image path."""
        self.plotter._frame_for_video.extend(["a.png", "b.png"])
        self.plotter.clean_frame_for_video()
        self.assertEqual(self.plotter._frame_for_video, [])
