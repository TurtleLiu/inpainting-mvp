from pathlib import Path
from PIL import Image, UnidentifiedImageError
import io
import re
from .config import config


SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]")


def sanitize_filename(name: str) -> str:
    name = Path(name).name
    return SAFE_NAME_RE.sub("_", name)


def validate_image_bytes(content: bytes) -> None:
    if len(content) > config.max_upload_bytes:
        raise ValueError("File too large")
    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
        with Image.open(io.BytesIO(content)) as img2:
            width, height = img2.size
            if width * height > config.max_pixels:
                raise ValueError("Image too large in pixels")
    except UnidentifiedImageError:
        raise ValueError("Invalid image")
    except OSError:
        raise ValueError("Invalid image")