from PIL import Image
import numpy as np
import cv2


def grabcut_mask(image: Image.Image, bbox: tuple) -> Image.Image:
    img = np.array(image)
    
    x1, y1, x2, y2 = bbox
    width, height = image.size
    
    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(1, min(x2, width))
    y2 = max(1, min(y2, height))
    
    mask = np.zeros(img.shape[:2], np.uint8)
    mask[y1:y2, x1:x2] = 255
    
    return Image.fromarray(mask)