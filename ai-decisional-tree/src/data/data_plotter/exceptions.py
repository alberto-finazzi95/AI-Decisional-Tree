"""
@brief Define errors raised when a requested video lacks expected frames.
"""


class NotEnoughPngFiles(Exception):
    """
    @brief Raised when collected PNG frames do not match the expected count.
    """

    def __init__(self, patient_id: str, num_frame_read: int, num_frame_expected: int):
        """
        @brief Create an error describing the actual and expected video frame counts.
        @param patient_id: Study identifier.
        @param num_frame_read: Num frame read used by this operation.
        @param num_frame_expected: Expected frame count.
        """
        super().__init__(
            f"[Patient {patient_id}] Not enough png files: {num_frame_read} read, but expected " f"{num_frame_expected}"
        )
