import unittest

import numpy as np
import pandas as pd
import src.volume_manager as vm
import src.volume_manager.data_structures as ds


class VolumeManagerTests(unittest.TestCase):
    """Tests slice buffering, volume statistics, voxel extraction, and cleanup."""

    CENTER_NEIGHBORHOOD_COLUMN: str = "pixel_x_0_y_0_z_0"

    def setUp(self):
        self.manager: vm.VolumeManager = vm.VolumeManager()

    def test_add_and_build_assemble_volumes_and_dimensions(self):
        """Verify buffered image and mask slices form volumes with correct dimensions."""
        image = np.ones((4, 5), dtype=np.float32)
        mask = np.zeros((4, 5), dtype=np.uint8)
        self.manager.add_img(image)
        self.manager.add_msk(mask)

        self.assertEqual(self.manager.num_slices, 1)
        self.manager.build()

        np.testing.assert_array_equal(self.manager.vol_img, image[np.newaxis, ...])
        np.testing.assert_array_equal(self.manager.vol_msk, mask[np.newaxis, ...])
        self.assertEqual((self.manager.z, self.manager.y, self.manager.x), (1, 4, 5))

    def test_build_extracts_nonzero_interior_voxel_and_neighborhood(self):
        """Check that a valid voxel produces its label, local statistics, and neighbors."""
        image = np.zeros((3, 3, 3), dtype=np.float32)
        mask = np.zeros((3, 3, 3), dtype=np.uint8)
        image[1, 1, 1] = 9
        mask[1, 1, 1] = 2
        for image_slice, mask_slice in zip(image, mask, strict=True):
            self.manager.add_img(image_slice)
            self.manager.add_msk(mask_slice)

        self.manager.build()
        records = self.manager.records

        self.assertEqual(len(records), 1)
        self.assertEqual(records.loc[0, ds.ParamEnum.META_NORM], np.float32(1 / 3))
        self.assertEqual(records.loc[0, ds.ParamEnum.TARGET], 2)
        self.assertEqual(records.loc[0, self.CENTER_NEIGHBORHOOD_COLUMN], 9)
        self.assertEqual(records.loc[0, "pixel_x_1_y_0_z_0"], 0)
        self.assertIn(ds.ParamEnum.STAT_MEAN_3D, records.columns)
        self.assertIn(ds.ParamEnum.STAT_MEAN_STD, records.columns)

    def test_voxel_is_retained_when_only_adjacent_slice_is_nonzero(self):
        """Ensure a voxel is retained when image activity is in an adjacent slice."""
        image = np.zeros((3, 3, 3), dtype=np.float32)
        mask = np.zeros((3, 3, 3), dtype=np.uint8)
        image[0, 1, 1] = 4
        mask[1, 1, 1] = 1
        for image_slice, mask_slice in zip(image, mask, strict=True):
            self.manager.add_img(image_slice)
            self.manager.add_msk(mask_slice)

        self.manager.build()

        self.assertEqual(len(self.manager.records), 1)
        self.assertEqual(self.manager.records.loc[0, ds.ParamEnum.TARGET], 1)

    def test_empty_volume_records_have_expected_schema(self):
        """Verify an all-zero volume produces no records but retains output columns."""
        self.manager.add_img(np.zeros((3, 3), dtype=np.float32))
        self.manager.add_msk(np.zeros((3, 3), dtype=np.uint8))

        self.manager.build()

        self.assertTrue(self.manager.records.empty)
        self.assertIn(ds.ParamEnum.TARGET, self.manager.records.columns)
        self.assertIn(self.CENTER_NEIGHBORHOOD_COLUMN, self.manager.records.columns)

    def test_local_mean_and_standard_deviation_for_constant_volume(self):
        """Check local statistics return the constant value and zero deviation."""
        self.manager._vol_img = np.full((3, 3, 3), 5, dtype=np.float32)
        np.testing.assert_allclose(self.manager.mean_volume, 5)
        np.testing.assert_allclose(self.manager.std_volume, 0)

    def test_clean_volume_methods_reset_only_their_own_state(self):
        """Verify clearing image and mask volumes leaves the other volume untouched."""
        self.manager.add_img(np.ones((3, 3)))
        self.manager.add_msk(np.ones((3, 3)))
        self.manager.build()

        self.manager.clean_vol_img()
        self.assertEqual(self.manager.num_slices, 0)
        self.assertEqual(self.manager.vol_img.size, 0)
        self.assertEqual(self.manager.vol_msk.size, 9)

        self.manager.clean_vol_msk()
        self.assertEqual(self.manager.vol_msk.size, 0)

    def test_clean_resets_all_buffers_volumes_dimensions_and_records(self):
        """Ensure clean resets slice buffers, volumes, dimensions, and records."""
        self.manager.add_img(np.ones((3, 3)))
        self.manager.add_msk(np.ones((3, 3)))
        self.manager.build()

        self.manager.clean()

        self.assertEqual(self.manager.num_slices, 0)
        self.assertEqual((self.manager.x, self.manager.y, self.manager.z), (0, 0, 0))
        self.assertEqual(self.manager.vol_img.size, 0)
        self.assertEqual(self.manager.vol_msk.size, 0)
        self.assertIsInstance(self.manager.records, pd.DataFrame)
        self.assertTrue(self.manager.records.empty)
