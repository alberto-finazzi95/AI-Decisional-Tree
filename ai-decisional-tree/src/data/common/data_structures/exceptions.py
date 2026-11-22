"""
@brief Define custom exceptions for data structure validation.
"""


class InvalidTimeRange(ValueError):
    """
    @brief Raised when a study's time range is not formatted correctly.
    @param time: The invalid time range string.
    """

    def __init__(self, time: str):
        super().__init__(f"Invalid time range format: {time}")
