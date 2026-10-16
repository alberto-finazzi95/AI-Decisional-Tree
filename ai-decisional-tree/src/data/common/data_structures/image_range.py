from dataclasses import dataclass


@dataclass(frozen=True)
class ImageRange:
    lim_inf: float
    lim_sup: float
