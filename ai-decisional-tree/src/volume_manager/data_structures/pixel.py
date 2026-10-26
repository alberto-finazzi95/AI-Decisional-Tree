from dataclasses import dataclass


@dataclass(frozen=True)
class Pixel:
    x: int
    y: int
    z: int

    @property
    def name(self) -> str:
        return f"pixel_x_{self.x}_y_{self.y}_z_{self.z}"
