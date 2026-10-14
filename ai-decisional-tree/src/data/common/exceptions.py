

class StudyNotFoundError(KeyError):
    def __init__(self, study_id: str):
        super().__init__(f"Study not found: {study_id}")


class IndexNotFoundError(IndexError):
    def __init__(self, subfolder_index: int, study_id: str):
        super().__init__(f"Subfolder index {subfolder_index} is out of range for study {study_id}.")
