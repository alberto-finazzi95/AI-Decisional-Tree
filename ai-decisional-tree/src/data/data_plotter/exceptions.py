

class NotEnoughPngFiles(Exception):
    def __init__(self, patient_id: str, num_frame_read: int, num_frame_expected: int):
        super().__init__(f"[Patient {patient_id}] Not enough png files: {num_frame_read} read, but expected "
                         f"{num_frame_expected}")