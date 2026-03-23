
import io
import pytest
from PIL import Image

from inpainting_app.config import AppConfig
from inpainting_app.security import validate_upload, validate_mask, sanitize_filename, SecurityError

def test_validate_upload_ok(sample_upload):
    img = validate_upload(sample_upload, AppConfig())
    assert img.size == (64, 64)

def test_reject_bad_filename():
    with pytest.raises(SecurityError):
        sanitize_filename("../evil.png")

def test_reject_non_image():
    bio = io.BytesIO(b"not an image")
    bio.name = "x.txt"
    with pytest.raises(SecurityError):
        validate_upload(bio, AppConfig())

def test_mask_size_mismatch(sample_mask_upload):
    img = Image.new("RGB", (128, 128), "white")
    with pytest.raises(SecurityError):
        validate_mask(sample_mask_upload, img.size, AppConfig())
