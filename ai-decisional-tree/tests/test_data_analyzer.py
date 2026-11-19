import unittest
from unittest.mock import Mock, patch

import numpy as np
import src.data.data_analyzer.data_analyzer as da

import tests.helper as h


class DataAnalyzerTests(unittest.TestCase):
    """Tests window bounds and delegation of frame filtering and persistence."""

    FRAME_PATH: str = "study/frame"
    IMAGE_MANAGER_METHOD: str = "get_img_manager"
    FILTER_ERROR: str = "invalid image"

    def setUp(self):
        _, self.folder_manager, self.config_parser = h.make_data_dependencies()
        self.analyzer: da.DataAnalyzer = da.DataAnalyzer(self.folder_manager, self.config_parser)

    def test_brain_window_bounds_match_window_level_and_width(self):
        """Verify the brain window bounds are derived from its level and width."""
        self.assertEqual(self.analyzer.br_w_inf, 0)
        self.assertEqual(self.analyzer.br_w_sup, 80)

    def test_filter_frame_filters_stores_and_saves_filtered_image(self):
        """Check that a frame is filtered with configured parameters and persisted."""
        image_matrix = np.array([[0, 40], [80, 120]])
        img_manager: Mock = Mock()
        img_manager.img_flt_matrix = image_matrix
        with patch.object(self.analyzer, self.IMAGE_MANAGER_METHOD, return_value=img_manager) as get_manager:
            self.analyzer.filter_frame(self.FRAME_PATH)

        get_manager.assert_called_once_with(self.FRAME_PATH)
        img_manager.filer_img.assert_called_once_with(0.0, 80.0, self.analyzer.MED_W)
        self.assertIs(self.analyzer._img_filtered, image_matrix)
        img_manager.save_filter_img.assert_called_once_with()

    def test_filter_frame_propagates_filter_failures_without_saving(self):
        """Ensure filtering errors propagate and prevent saving a failed result."""
        img_manager = Mock()
        img_manager.filer_img.side_effect = ValueError(self.FILTER_ERROR)
        with patch.object(self.analyzer, self.IMAGE_MANAGER_METHOD, return_value=img_manager):
            with self.assertRaisesRegex(ValueError, self.FILTER_ERROR):
                self.analyzer.filter_frame(self.FRAME_PATH)
        img_manager.save_filter_img.assert_not_called()
