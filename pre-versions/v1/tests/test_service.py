
import pytest
from inpainting_app.config import AppConfig
from inpainting_app.service import InpaintingService

def test_service_run_success(sample_image, sample_mask):
    svc = InpaintingService(AppConfig())
    result = svc.run(sample_image, sample_mask, algorithm="ns", radius=5, max_edge=128)
    assert result.output_image.size == (64, 64)

def test_service_invalid_algorithm(sample_image, sample_mask):
    svc = InpaintingService(AppConfig())
    with pytest.raises(ValueError):
        svc.run(sample_image, sample_mask, algorithm="bad", radius=5, max_edge=128)

def test_service_invalid_radius(sample_image, sample_mask):
    svc = InpaintingService(AppConfig())
    with pytest.raises(ValueError):
        svc.run(sample_image, sample_mask, algorithm="telea", radius=0, max_edge=128)
