"""
@brief Define errors raised when image-state configuration is unavailable.
"""
class ImageStateToolkitNotFound(KeyError):
    """
    @brief Raised when no toolkit is configured for an image state.
    """
    def __init__(self, state: str):
        """
        @brief Create an error identifying the image state without a toolkit.
        @param state: State used by this operation.
        """
        super().__init__(f"Image state '{state}' not found in state dict")
