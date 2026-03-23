import os
from dataclasses import dataclass


@dataclass
class Config:
    max_upload_bytes: int = 10 * 1024 * 1024
    max_pixels: int = 4096 * 4096
    inpaint_backend: str = os.getenv("INPAINT_BACKEND", "opencv")
    diffusers_model_id: str = os.getenv("DIFFUSERS_MODEL_ID", "runwayml/stable-diffusion-inpainting")


config = Config()