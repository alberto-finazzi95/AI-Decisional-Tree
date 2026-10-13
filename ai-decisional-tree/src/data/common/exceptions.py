

class StudyNotFoundError(KeyError):
    def __init__(self, study_id: str):
        super().__init__(f"Study not found: {study_id}")
