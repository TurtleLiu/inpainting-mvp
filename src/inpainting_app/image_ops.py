from typing import Optional
from PIL import Image
import numpy as np
import cv2

try:
    import torch
    from diffusers import StableDiffusionInpaintPipeline
except Exception:
    torch = None
    StableDiffusionInpaintPipeline = None

from .config import config

_PIPE = None

def _load_diffusers():
    global _PIPE
    if _PIPE is None:
        if StableDiffusionInpaintPipeline is None:
            raise RuntimeError("Diffusers backend unavailable")
        dtype = torch.float16 if torch and torch.cuda.is_available() else torch.float32
        _PIPE = StableDiffusionInpaintPipeline.from_pretrained(
            config.diffusers_model_id, torch_dtype=dtype
        )
        if torch and torch.cuda.is_available():
            _PIPE = _PIPE.to("cuda")
    return _PIPE

def normalize_mask(mask_arr: np.ndarray) -> np.ndarray:
    if mask_arr.ndim == 3:
        mask_arr = cv2.cvtColor(mask_arr, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(mask_arr, 127, 255, cv2.THRESH_BINARY)
    return binary

def inpaint_opencv(image_path: str, mask_path: str, method: str = "telea") -> Image.Image:
    img = cv2.imread(image_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if img is None or mask is None:
        raise ValueError("Failed to load image or mask")
    mask = normalize_mask(mask)
    flag = cv2.INPAINT_TELEA if method == "telea" else cv2.INPAINT_NS
    out = cv2.inpaint(img, mask, 3, flag)
    out = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    return Image.fromarray(out)

def inpaint_diffusers(image_path: str, mask_path: str, prompt: Optional[str] = None) -> Image.Image:
    pipe = _load_diffusers()
    image = Image.open(image_path).convert("RGB")
    mask = Image.open(mask_path).convert("RGB")
    result = pipe(
        prompt=prompt or "clean natural image completion",
        image=image,
        mask_image=mask,
        num_inference_steps=20,
        guidance_scale=7.5,
    ).images[0]
    return result