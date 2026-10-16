

class ImageStateToolkitNotFound(KeyError):
    def __init__(self, state: str):
        super().__init__(f"Image state '{state}' not found in state dict")
