
import io
from PIL import Image
import pytest

@pytest.fixture
def sample_image():
    img = Image.new("RGB", (64, 64), "white")
    for x in range(20, 44):
        for y in range(20, 44):
            img.putpixel((x, y), (255, 0, 0))
    return img

@pytest.fixture
def sample_mask():
    mask = Image.new("L", (64, 64), 0)
    for x in range(24, 40):
        for y in range(24, 40):
            mask.putpixel((x, y), 255)
    return mask

def pil_to_upload(img, fmt="PNG", name="file.png"):
    bio = io.BytesIO()
    img.save(bio, format=fmt)
    bio.name = name
    bio.seek(0)
    return bio

@pytest.fixture
def sample_upload(sample_image):
    return pil_to_upload(sample_image, "PNG", "image.png")

@pytest.fixture
def sample_mask_upload(sample_mask):
    return pil_to_upload(sample_mask.convert("RGB"), "PNG", "mask.png")
