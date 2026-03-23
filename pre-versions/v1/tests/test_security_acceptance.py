
import io
import pytest
from PIL import Image

from inpainting_app.config import AppConfig
from inpainting_app.security import validate_upload, SecurityError

def test_security_large_file_rejected():
    # simulate policy with very small threshold
    cfg = AppConfig(max_upload_mb=0, max_pixels=4096*4096)
    img = Image.new("RGB", (64,64), "white")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.name = "image.png"
    bio.seek(0)
    with pytest.raises(SecurityError):
        validate_upload(bio, cfg)

def test_security_pixel_limit_rejected():
    cfg = AppConfig(max_upload_mb=10, max_pixels=100)
    img = Image.new("RGB", (64,64), "white")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.name = "image.png"
    bio.seek(0)
    with pytest.raises(SecurityError):
        validate_upload(bio, cfg)
