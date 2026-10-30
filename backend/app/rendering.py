"""Deterministic SKU-preserving concept renderer; never generates substitute products."""
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

MAX_BYTES = 12 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 25_000_000

def decode_image(data: bytes):
    from io import BytesIO
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Image must be between 1 byte and 12 MB')
    try:
        with Image.open(BytesIO(data)) as original:
            if original.format not in ('JPEG', 'PNG', 'WEBP'):
                raise ValueError('Use JPEG, PNG or WebP')
            if original.width * original.height > 25_000_000:
                raise ValueError('Image exceeds 25 megapixels')
            original.load()
            image=ImageOps.exif_transpose(original).convert('RGBA')
            image.info.clear()
            return image
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('Invalid or oversized image') from exc

def render(room, assets, media: Path, output: Path, model_images=None):
    canvas = room.copy()
    canvas.thumbnail((1600, 1200))
    width, height = canvas.size
    placements = []
    # Concept staging: floor-aligned product overlays, not inferred room geometry.
    for i, asset in enumerate(assets):
        reference=(model_images or {}).get(asset.id,asset.image_url)
        path = media / reference.rsplit('/', 1)[-1]
        product = decode_image(path.read_bytes())
        scale_width = min(width * .40, width * asset.width_cm / 500)
        product.thumbnail((max(1, int(scale_width)), max(1, int(height * .55))))
        center = width * ((i + 1) / (len(assets) + 1))
        x = max(0, min(width-product.width, int(center-product.width/2)))
        y = int(height * .88) - product.height
        shadow = Image.new('RGBA', canvas.size)
        alpha = product.getchannel('A').resize((product.width, max(1, int(product.height*.12))))
        blob = Image.new('RGBA', alpha.size, (0,0,0,100)); blob.putalpha(alpha.point(lambda p: int(p*.3)))
        shadow.alpha_composite(blob, (x, min(height-blob.height, y+product.height-8)))
        canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(12)))
        canvas.alpha_composite(product, (x,y))
        placements.append({'asset_id':asset.id,'x':x,'y':y,'width':product.width,'height':product.height,'quantity':1,'reference_source':'seller_photograph' if (model_images or {}).get(asset.id) else 'product_photo'})
    canvas.convert('RGB').save(output, 'JPEG', quality=92)
    return placements
