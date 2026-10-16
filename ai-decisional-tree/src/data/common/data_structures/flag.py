from dataclasses import dataclass


@dataclass(frozen=True)
class Flag:
    img: bool
    video: bool

    def all_media_disabled(self) -> bool:
        return (not self.img) and (not self.video)
