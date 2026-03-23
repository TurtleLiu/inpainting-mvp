
from inpainting_app.config import AppConfig
from inpainting_app.security import validate_upload, validate_mask
from inpainting_app.service import InpaintingService

def test_end_to_end_acceptance(sample_upload, sample_mask_upload):
    cfg = AppConfig()
    img = validate_upload(sample_upload, cfg)
    mask = validate_mask(sample_mask_upload, img.size, cfg)
    svc = InpaintingService(cfg)
    result = svc.run(img, mask, algorithm="telea", radius=3, max_edge=256)
    assert result.output_image.size == img.size
    assert result.meta["masked_pixels"] > 0
