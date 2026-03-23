from typing import Optional
from PIL import Image
from .image_ops import inpaint_opencv, inpaint_diffusers
from .security import validate_image_bytes
import io


class InpaintingService:
    def __init__(self):
        pass
    
    def inpaint(self, image_path: str, mask_path: str, backend: str = "opencv", method: str = "telea", prompt: Optional[str] = None) -> Image.Image:
        if backend == "diffusers":
            return inpaint_diffusers(image_path, mask_path, prompt=prompt)
        return inpaint_opencv(image_path, mask_path, method=method)
    
    def validate_image(self, image_bytes: bytes) -> None:
        validate_image_bytes(image_bytes)
    
    def process_image_from_bytes(self, image_bytes: bytes, mask_bytes: bytes, backend: str = "opencv", method: str = "telea", prompt: Optional[str] = None) -> Image.Image:
        self.validate_image(image_bytes)
        self.validate_image(mask_bytes)
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_file:
            img_file.write(image_bytes)
            img_path = img_file.name
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as mask_file:
            mask_file.write(mask_bytes)
            mask_path = mask_file.name
        
        try:
            result = self.inpaint(img_path, mask_path, backend, method, prompt)
            return result
        finally:
            import os
            os.unlink(img_path)
            os.unlink(mask_path)