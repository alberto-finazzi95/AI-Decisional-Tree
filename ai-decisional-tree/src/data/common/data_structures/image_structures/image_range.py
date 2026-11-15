"""
@brief Represent the lower and upper image intensity limits.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ImageRange:
    """
    @brief Inclusive image intensity bounds used for plotting.
    """
    lim_inf: float
    lim_sup: float
