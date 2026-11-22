from dataclasses import dataclass


@dataclass(frozen=True)
class TimeRange:
    """
    @brief Represents a time range with lower and upper bounds.
    """

    lower: float
    upper: float

    def __str__(self) -> str:
        """
        @brief Return a string representation of the time range.
        @return: The value produced by this operation.
        """
        return f"{self.lower}-{self.upper}"
