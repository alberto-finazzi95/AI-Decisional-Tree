from dataclasses import dataclass
from typing import Callable

import src.data.common.data_structures.image_structures.flag as f
import src.data.common.data_structures.image_structures.image_range as ir


@dataclass(frozen=True)
class ImageStateToolkit:
    flag: f.Flag
    create_tac_fn: Callable
    store_tac_png_fn: Callable
    store_tac_video_fn: Callable
    img_range: ir.ImageRange
