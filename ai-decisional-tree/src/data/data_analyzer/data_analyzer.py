"""
@brief Apply configured image windowing and filtering to study frames.
"""
import numpy as np

import src.common as cm
import src.config_parser as cp
import src.data.common as dcm
import src.image_manager as im


class DataAnalyzer(dcm.BaseData):
    # BRAIN WINDOWING (Isolation interval 0-80 HU)
    """
    @brief Window, median-filter, and save study image frames.
    """
    BR_W_L: int = 40
    BR_W_W: int = 80
    # Median filer window size
    MED_W: int = 3

    def __init__(
        self,
        folder_manager: cm.FolderManager,
        config_parser: cp.ConfigParser,
        os_manager: cm.OsManager | None = None,
    ):
        """
        @brief Initialize shared data paths and image-analysis settings.
        @param folder_manager: Folder manager used for filesystem operations.
        @param config_parser: Parser providing dataset and output settings.
        @param os_manager: Optional filesystem-operation implementation.
        """
        super().__init__(folder_manager=folder_manager, config_parser=config_parser, os_manager=os_manager)
        self._img_filtered: np.ndarray = np.ndarray([])

    @property
    def br_w_inf(self) -> float:
        """
        @brief Return the lower bound of the configured brain window.
        @return: The float produced by this operation.
        """
        return self.BR_W_L - (self.BR_W_W / 2.0)

    @property
    def br_w_sup(self) -> float:
        """
        @brief Return the upper bound of the configured brain window.
        @return: The float produced by this operation.
        """
        return self.BR_W_L + (self.BR_W_W / 2.0)

    def filter_frame(self, img_path: str):
        # Load the image manager
        """
        @brief Filter a frame and persist its filtered image matrix.
        @param img_path: Path to the image or patient frame.
        """
        img_manager: im.ImageManager = self.get_img_manager(img_path)
        # Filter the image
        img_manager.filer_img(self.br_w_inf, self.br_w_sup, self.MED_W)
        # Save the image filtered in the variable
        self._img_filtered = img_manager.img_flt_matrix
        # Store as npz file the image filtered
        img_manager.save_filter_img()
