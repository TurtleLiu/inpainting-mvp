
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    max_upload_mb: int = 10
    max_pixels: int = 4096 * 4096
    allowed_formats: tuple[str, ...] = ("PNG", "JPEG", "WEBP")
