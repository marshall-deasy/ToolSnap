"""QR code generation for tooling cabinet location labels."""

from pathlib import Path

import qrcode
from qrcode.image.pil import PilImage
from PIL import Image, ImageDraw, ImageFont

from config import get as cfg_get


def generate_qr_image(
    location_id: str,
    size_mm: int | None = None,
    include_text: bool = True,
) -> Image.Image:
    """Generate a QR code image for a location ID.

    Args:
        location_id: The location string, e.g. "CAB-03:DWR-07"
        size_mm: Label size in mm (controls output resolution)
        include_text: Whether to add the location text below the QR code

    Returns:
        PIL Image ready for display or printing.
    """
    prefix = cfg_get("qr_label_prefix", "TS")
    full_code = f"{prefix}:{location_id}"

    if size_mm is None:
        size_mm = cfg_get("qr_label_size_mm", 30)

    # Generate QR at a resolution suitable for printing (~300 DPI)
    # size_mm at 300 DPI → pixels
    target_px = int(size_mm * 300 / 25.4)

    qr = qrcode.QRCode(
        version=None,  # auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(full_code)
    qr.make(fit=True)
    qr_img: Image.Image = qr.make_image(fill_color="black", back_color="white").get_image()

    if not include_text:
        return qr_img.resize((target_px, target_px), Image.NEAREST)

    # Add text label below QR code
    qr_size = target_px
    text_height = int(target_px * 0.15)
    total_height = qr_size + text_height

    result = Image.new("RGB", (qr_size, total_height), "white")
    qr_resized = qr_img.resize((qr_size, qr_size), Image.NEAREST)
    result.paste(qr_resized, (0, 0))

    draw = ImageDraw.Draw(result)
    try:
        font_size = max(12, text_height - 4)
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), full_code, font=font)
    text_w = bbox[2] - bbox[0]
    text_x = (qr_size - text_w) // 2
    text_y = qr_size + 2
    draw.text((text_x, text_y), full_code, fill="black", font=font)

    return result


def save_qr_image(location_id: str, output_path: Path, **kwargs) -> Path:
    """Generate and save a QR label image to disk."""
    img = generate_qr_image(location_id, **kwargs)
    output_path = output_path.with_suffix(".png")
    img.save(str(output_path), "PNG")
    return output_path
