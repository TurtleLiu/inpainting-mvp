
from inpainting_app.image_ops import inpaint_image, prepare_mask

def test_prepare_mask_binary(sample_mask):
    out = prepare_mask(sample_mask)
    vals = set(out.getdata())
    assert vals.issubset({0, 255})

def test_inpaint_returns_image(sample_image, sample_mask):
    result = inpaint_image(sample_image, sample_mask, algorithm="telea", radius=3, max_edge=128)
    assert result.output_image.size == sample_image.size
    assert result.meta["algorithm"] == "telea"
    assert result.meta["masked_pixels"] > 0
