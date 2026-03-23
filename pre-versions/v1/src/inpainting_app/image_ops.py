
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np
from PIL import Image

Algorithm = Literal["telea", "ns"]


@dataclass
class InpaintOutput:
    output_image: Image.Image
    meta: dict


def resize_keep_ratio(img: Image.Image, max_edge: int) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_edge:
        return img
    ratio = max_edge / max(w, h)
    new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
    return img.resize(new_size)


def prepare_mask(mask: Image.Image) -> Image.Image:
    arr = np.array(mask.convert("L"))
    # threshold to binary
    arr = np.where(arr > 127, 255, 0).astype("uint8")
    return Image.fromarray(arr, mode="L")


def inpaint_image(
    image: Image.Image,
    mask: Image.Image,
    algorithm: Algorithm = "telea",
    radius: int = 3,
    max_edge: int = 1024,
) -> InpaintOutput:
    img_rs = resize_keep_ratio(image.convert("RGB"), max_edge=max_edge)
    mask_rs = resize_keep_ratio(prepare_mask(mask), max_edge=max_edge)

    if img_rs.size != mask_rs.size:
        mask_rs = mask_rs.resize(img_rs.size)

    img_bgr = cv2.cvtColor(np.array(img_rs), cv2.COLOR_RGB2BGR)
    mask_np = np.array(mask_rs)

    flag = cv2.INPAINT_TELEA if algorithm == "telea" else cv2.INPAINT_NS
    out_bgr = cv2.inpaint(img_bgr, mask_np, radius, flag)
    out_rgb = cv2.cvtColor(out_bgr, cv2.COLOR_BGR2RGB)
    meta = {
        "algorithm": algorithm,
        "radius": radius,
        "input_size": list(image.size),
        "processed_size": list(img_rs.size),
        "masked_pixels": int((mask_np > 0).sum()),
    }
    return InpaintOutput(output_image=Image.fromarray(out_rgb), meta=meta)
