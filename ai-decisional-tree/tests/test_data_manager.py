import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, call

import numpy as np
import pandas as pd
import src.common as cm
import src.data.common as dcm
import src.data.data_manager.data_manager as dm
import src.data.data_manager.exceptions as ex

import tests.helper as h


class DataManagerTests(unittest.TestCase):
    """Tests orchestration of dataset state, image callbacks, and volume storage."""

    STUDY_ID: str = "study-1"
    SECOND_STUDY_ID: str = "study-2"
    STUDY_PATH: str = "study"
    FRAME_PATH: str = "study/frame"

    def setUp(self):
        _, self.folder_manager, self.config_parser = h.make_data_dependencies()
        self.data_loader: Mock = Mock()
        self.data_plotter: Mock = Mock()
        self.data_analyzer: Mock = Mock()
        self.data_analyzer.br_w_inf = 0
        self.data_analyzer.br_w_sup = 80
        self.toolkit = SimpleNamespace(
            folder_manager=self.folder_manager,
            config_parser=self.config_parser,
            data_loader=self.data_loader,
            data_plotter=self.data_plotter,
            data_analyzer=self.data_analyzer,
            reset_img_manager_dict=Mock(),
        )
        self.manager = dm.DataManager(self.toolkit)

    def test_initialization_loads_and_processes_data_and_sets_default_states(self):
        """Verify initialization loads dataset metadata and selects raw training data."""
        self.data_loader.load_data.assert_called_once_with()
        self.data_loader.process_data.assert_called_once_with()
        self.assertEqual(self.manager.state, dcm.DatasetType.TRAIN)
        self.assertEqual(self.manager.img_range, dcm.ImageRange(lim_inf=0, lim_sup=80))
        self.assertTrue(self.manager.flag.img)
        self.assertTrue(self.manager.flag.video)

    def test_state_and_image_state_toolkits_expose_configured_callbacks(self):
        """Check state changes select matching flags, ranges, and callback functions."""
        self.manager.state = dcm.DatasetType.TEST
        self.manager._image_state = dcm.ImageState.FILTER
        self.assertEqual(self.manager.state, dcm.DatasetType.TEST)
        self.assertEqual(self.manager.flag, dcm.Flag(img=False, video=False))
        self.assertEqual(self.manager.img_range, dcm.ImageRange(lim_inf=0, lim_sup=1))
        self.assertEqual(self.manager.create_tac_fn, self.manager.create_filter_tac)
        self.assertEqual(self.manager.store_tac_png_fn, self.manager.store_tac_filter_png)
        self.assertEqual(self.manager.store_tac_video_fn, self.manager.store_tac_filter_video)

    def test_check_flag_reports_when_both_media_outputs_are_disabled(self):
        """Ensure the output check reflects whether both media types are disabled."""
        self.manager._image_state = dcm.ImageState.FILTER
        self.assertTrue(self.manager.check_flag())
        self.manager._image_state = dcm.ImageState.RAW
        self.assertFalse(self.manager.check_flag())

    def test_disabled_filtered_media_skips_study_iteration(self):
        """Verify disabled filtered output returns before looking up any studies."""
        self.manager.create_all_tacs_filtered()
        self.data_loader.get_study_catalog.assert_not_called()
        self.toolkit.reset_img_manager_dict.assert_not_called()

    def test_media_pipeline_invokes_selected_callbacks_for_each_frame(self):
        """Check enabled raw output renders and stores every frame and its video."""
        studies = (SimpleNamespace(study_id=self.STUDY_ID, num_subfolders=2),)
        self.data_loader.get_study_catalog.return_value.studies = studies
        create_tac = Mock()
        store_png = Mock()
        store_video = Mock()
        self.manager._IMG_STATE_TLK_DICT[dcm.ImageState.RAW] = replace(
            self.manager._IMG_STATE_TLK_DICT[dcm.ImageState.RAW],
            create_tac_fn=create_tac,
            store_tac_png_fn=store_png,
            store_tac_video_fn=store_video,
        )

        self.manager.create_all_tacs()

        self.assertEqual(create_tac.call_args_list, [call(self.STUDY_ID, 0), call(self.STUDY_ID, 1)])
        self.assertEqual(store_png.call_args_list, [call(self.STUDY_ID, 0), call(self.STUDY_ID, 1)])
        store_video.assert_called_once_with(self.STUDY_ID, 2)
        self.toolkit.reset_img_manager_dict.assert_called_once_with()

    def test_create_volume_tacs_concatenates_and_stores_each_study(self):
        """Verify volume generation appends each frame and stores once per study."""
        studies = (
            SimpleNamespace(study_id=self.STUDY_ID, num_subfolders=2),
            SimpleNamespace(study_id=self.SECOND_STUDY_ID, num_subfolders=0),
        )
        self.data_loader.get_study_catalog.return_value.studies = studies
        self.manager.concatenate_tac = Mock()
        self.manager.store_volume_tac = Mock()

        self.manager.create_volume_tacs()

        self.assertEqual(
            self.manager.concatenate_tac.call_args_list,
            [call(self.STUDY_ID, 0), call(self.STUDY_ID, 1)],
        )
        self.assertEqual(
            self.manager.store_volume_tac.call_args_list,
            [call(self.STUDY_ID), call(self.SECOND_STUDY_ID)],
        )

    def test_concatenate_tac_loads_and_adds_image_and_mask(self):
        """Check a frame's image and mask are loaded and added to volume buffers."""
        image, mask = np.ones((2, 2)), np.zeros((2, 2))
        self.manager.get_patient_img_path = Mock(return_value=self.FRAME_PATH)
        self.data_plotter.load_matrices.return_value = (image, mask)
        self.manager._volume_manager.add_img = Mock()
        self.manager._volume_manager.add_msk = Mock()

        self.manager.concatenate_tac(self.STUDY_PATH, 3)

        self.manager.get_patient_img_path.assert_called_once_with(self.STUDY_PATH, 3)
        self.data_plotter.load_matrices.assert_called_once_with(self.FRAME_PATH)
        self.manager._volume_manager.add_img.assert_called_once_with(image)
        self.manager._volume_manager.add_msk.assert_called_once_with(mask)

    def test_store_volume_builds_persists_and_cleans_volume(self):
        """Ensure volume records are built, saved for the active split, and cleared."""
        records = pd.DataFrame({"target": [1]})
        volume_manager = Mock()
        volume_manager.records = records
        self.manager._volume_manager = volume_manager

        self.manager.store_volume_tac(self.STUDY_PATH)

        volume_manager.build.assert_called_once_with()
        self.data_loader.store_volume.assert_called_once_with(records, self.STUDY_PATH, dcm.DatasetType.TRAIN)
        volume_manager.clean.assert_called_once_with()

    def test_get_patient_image_path_raises_for_missing_frame_folder(self):
        """Verify resolving a nonexistent frame folder raises the filesystem error."""
        self.manager.get_subfolders = Mock(return_value=(self.FRAME_PATH,))
        self.manager.path_exists = Mock(return_value=False)
        with self.assertRaisesRegex(cm.NoFolderFound, self.FRAME_PATH):
            self.manager.get_patient_img_path(self.STUDY_PATH, 0)

    def test_video_callbacks_skip_disabled_output_and_route_enabled_output(self):
        """Check disabled videos are skipped and enabled videos use the raw output path."""
        self.manager._image_state = dcm.ImageState.RAW
        self.manager._IMG_STATE_TLK_DICT[dcm.ImageState.RAW] = replace(
            self.manager._IMG_STATE_TLK_DICT[dcm.ImageState.RAW],
            flag=dcm.Flag(img=True, video=False),
        )
        self.manager.store_tac_video(self.STUDY_PATH, 2)
        self.data_plotter.save_video.assert_not_called()

        self.manager._IMG_STATE_TLK_DICT[dcm.ImageState.RAW] = replace(
            self.manager._IMG_STATE_TLK_DICT[dcm.ImageState.RAW],
            flag=dcm.Flag(img=True, video=True),
        )
        self.manager.store_tac_video(self.STUDY_PATH, 2)
        self.data_plotter.get_video_folder.assert_called_once_with(dcm.DatasetType.TRAIN)
        self.data_plotter.save_video.assert_called_once_with(
            self.STUDY_PATH, 2, self.data_plotter.get_video_folder.return_value
        )

    def test_invalid_image_state_raises_domain_error(self):
        """Ensure requesting an unsupported image state raises its domain error."""
        self.manager._image_state = "invalid"
        with self.assertRaises(ex.ImageStateToolkitNotFound):
            _ = self.manager.image_state_toolkit
