"""
@brief Define errors raised when study metadata cannot be resolved.
"""


class StudyNotFoundError(KeyError):
    """
    @brief Raised when a study identifier is absent from the catalog.
    """

    def __init__(self, study_id: str):
        """
        @brief Create a lookup error identifying the missing study.
        @param study_id: Unique study identifier.
        """
        super().__init__(f"Study not found: {study_id}")


class IndexNotFoundError(IndexError):
    """
    @brief Raised when a study subfolder index is out of range.
    """

    def __init__(self, subfolder_index: int, study_id: str):
        """
        @brief Create an index error identifying the study and invalid subfolder index.
        @param subfolder_index: Index of the subfolder within the study.
        @param study_id: Unique study identifier.
        """
        super().__init__(f"Subfolder index {subfolder_index} is out of range for study {study_id}.")
