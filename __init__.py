"""Nano Banana nodes for ComfyUI by Ace Data Cloud."""

from .nodes import (
    AceNanoBananaEdit, AceNanoBananaGenerate, AceNanoBananaLoadImage,
    AceNanoBananaLoadImages, AceNanoBananaRetrieve, AceNanoBananaRetrieveBatch,
)

NODE_CLASS_MAPPINGS = {
    "AceNanoBananaGenerate": AceNanoBananaGenerate,
    "AceNanoBananaEdit": AceNanoBananaEdit,
    "AceNanoBananaRetrieve": AceNanoBananaRetrieve,
    "AceNanoBananaRetrieveBatch": AceNanoBananaRetrieveBatch,
    "AceNanoBananaLoadImage": AceNanoBananaLoadImage,
    "AceNanoBananaLoadImages": AceNanoBananaLoadImages,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AceNanoBananaGenerate": "Nano Banana Generate Image (Ace Data Cloud)",
    "AceNanoBananaEdit": "Nano Banana Edit Image (Ace Data Cloud)",
    "AceNanoBananaRetrieve": "Nano Banana Retrieve Task (Ace Data Cloud)",
    "AceNanoBananaRetrieveBatch": "Nano Banana Retrieve Tasks (Ace Data Cloud)",
    "AceNanoBananaLoadImage": "Nano Banana Load Image (Ace Data Cloud)",
    "AceNanoBananaLoadImages": "Nano Banana Load Images (Ace Data Cloud)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
