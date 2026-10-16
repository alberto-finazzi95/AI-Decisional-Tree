from enum import StrEnum


class ImageFileType(StrEnum):
    IMG = "image.npz"
    MASK = "mask.npz"
    IMG_FLT = "image_filt.npz"
