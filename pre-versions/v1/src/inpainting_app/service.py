
from __future__ import annotations
from dataclasses import dataclass
from PIL import Image

from .config import AppConfig
from .image_ops import inpaint_image, InpaintOutput


class InpaintingService:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg

    def run(
        self,
        image: Image.Image,
        mask: Image.Image,
        *,
        algorithm: str = "telea",
        radius: int = 3,
        max_edge: int = 1024,
    ) -> InpaintOutput:
        if algorithm not in {"telea", "ns"}:
            raise ValueError("unsupported algorithm")
        if radius < 1 or radius > 50:
            raise ValueError("radius out of range")
        return inpaint_image(image, mask, algorithm=algorithm, radius=radius, max_edge=max_edge)
