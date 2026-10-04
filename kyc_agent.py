"""Validated image input and extraction-only output. No identity decisions."""
import argparse
import io
import warnings
from typing import Optional, Literal
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

MAX_BYTES = 10 * 1024 * 1024

class KYCData(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    id_number: Optional[str] = None
    readable: bool
    notes: str
    identity_verified: Literal[False] = False

def validate_image(data: bytes) -> str:
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Choose an image smaller than 10 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                fmt = image.format
                if fmt not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValueError('Choose a JPEG, PNG, or WebP image.')
                if image.width * image.height > 20_000_000:
                    raise ValueError('Image is too large. Use an image below 20 megapixels.')
                image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('This file is not a readable image.') from None
    return {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}[fmt]

def extract_bytes(data: bytes):
    from offline import extract_offline
    return extract_offline(data)

def extract_id_data(image_path: str):
    with open(image_path, 'rb') as source:
        return extract_bytes(source.read(MAX_BYTES + 1))

if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', help='Image to process locally with Tesseract')
    args = parser.parse_args()
    print(json.dumps(extract_id_data(args.image), ensure_ascii=False, indent=2))
