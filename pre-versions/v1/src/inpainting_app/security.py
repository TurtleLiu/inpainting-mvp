
from __future__ import annotations
import os
from pathlib import Path

from PIL import Image

from .config import AppConfig


class SecurityError(ValueError):
    """Raised when untrusted input fails validation."""


def _size_bytes(file_obj) -> int:
    pos = file_obj.tell()
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(pos)
    return size


def sanitize_filename(name: str) -> str:
    base = Path(name).name
    if base in {"", ".", ".."} or base != name:
        raise SecurityError("invalid filename")
    return base


def validate_upload(file_obj, cfg: AppConfig) -> Image.Image:
    sanitize_filename(getattr(file_obj, "name", "upload"))
    size = _size_bytes(file_obj)
    if size > cfg.max_upload_mb * 1024 * 1024:
        raise SecurityError("file too large")

    file_obj.seek(0)
    try:
        img = Image.open(file_obj)
        img.load()
        fmt = (img.format or "").upper()
    except Exception as e:
        raise SecurityError("unsupported or unsafe image type") from e
    finally:
        try:
            file_obj.seek(0)
        except Exception:
            pass

    if fmt not in cfg.allowed_formats:
        raise SecurityError("unsupported or unsafe image type")

    if (img.width * img.height) > cfg.max_pixels:
        raise SecurityError("image exceeds pixel limit")

    return img.convert("RGB")


def validate_mask(file_obj, expected_size: tuple[int, int], cfg: AppConfig) -> Image.Image:
    mask = validate_upload(file_obj, cfg).convert("L")
    if mask.size != expected_size:
        raise SecurityError("mask size must match input image size")
    return mask
