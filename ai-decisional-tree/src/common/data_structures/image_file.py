"""Enumeration of the canonical file names used for image-related artifacts.

This module centralizes the disk names of the main image files managed by the
project so that callers can reference them consistently instead of hard-coding
string literals throughout the codebase.

The values correspond to the compressed NumPy archives used to persist:
- the original image matrix,
- the segmentation mask,
- the filtered image output.
"""

from enum import StrEnum


class ImageFileType(StrEnum):
    """Canonical file types for image and mask artifacts.

    Each enum member represents a file name used by the imaging pipeline when
    reading or writing compressed arrays from disk.
    """

    IMG = "image.npz"
    """Path to the raw image matrix stored as a compressed NumPy archive."""

    MASK = "mask.npz"
    """Path to the segmentation mask stored as a compressed NumPy archive."""

    IMG_FLT = "image_filt.npz"
    """Path to the filtered image matrix stored as a compressed NumPy archive."""