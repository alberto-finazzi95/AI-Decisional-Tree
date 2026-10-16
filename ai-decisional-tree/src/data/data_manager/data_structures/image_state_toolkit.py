from dataclasses import dataclass
from typing import Callable

import src.data.data_manager.data_structures.flag as f


@dataclass(frozen=True)
class ImageStateToolkit:
    flag: f.Flag
    create_tac_fn: Callable
    store_tac_png_fn: Callable
    store_tac_video_fn: Callable
