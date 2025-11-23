# util/helpers.py
import base64
from io import BytesIO
from PIL import Image


# ------------------------------------------------------------
# Safe base64 decode
# ------------------------------------------------------------
def safe_b64decode(data_b64: str) -> bytes:
    try:
        if isinstance(data_b64, (bytes, bytearray)):
            return data_b64
        return base64.b64decode(data_b64)
    except Exception:
        return b""


# ------------------------------------------------------------
# Resize image (bytes -> PIL -> bytes)
# ------------------------------------------------------------
def image_resize(image_bytes: bytes, max_size: int = 900) -> bytes:
    try:
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail((max_size, max_size))
        out = BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return image_bytes


# ------------------------------------------------------------
# Resize image that is BASE64 encoded
# Acceptă bytes sau string base64
# ------------------------------------------------------------
def resize_image_b64(data, max_size: int = 900) -> str:
    try:
        # STEP 1 - detectăm dacă inputul este bytes sau string base64
        if isinstance(data, (bytes, bytearray)):
            img_bytes = data
        else:
            img_bytes = base64.b64decode(data)

        # STEP 2 - redimensionăm
        resized_bytes = image_resize(img_bytes, max_size=max_size)

        # STEP 3 - returnăm STRING BASE64 VALID
        return base64.b64encode(resized_bytes).decode()
    except Exception:
        # fallback: transformăm în STRING B64 ORICE PRIMIM
        try:
            return base64.b64encode(data).decode()
        except:
            return ""


# ------------------------------------------------------------
# Format multiline text
# ------------------------------------------------------------
def format_multiline(text: str) -> str:
    if not text:
        return ""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text.replace("\n", "<br/>")


# ------------------------------------------------------------
# Keep formatting
# ------------------------------------------------------------
def preformat(text: str) -> str:
    if not text:
        return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text


# ------------------------------------------------------------
# Prepare image for PDF (b64 -> scaled PIL -> BytesIO)
# ------------------------------------------------------------
def pdf_safe_image(b64_string: str, max_width_mm=150):
    try:
        img_data = base64.b64decode(b64_string)
        img = Image.open(BytesIO(img_data))

        # mm → px (approx 3.78 px per mm)
        max_w_px = int(max_width_mm * 3.78)

        w, h = img.size
        scale = min(max_w_px / w, 1.0)
        new_w = int(w * scale)
        new_h = int(h * scale)

        img = img.resize((new_w, new_h))

        out = BytesIO()
        img.save(out, format="PNG")
        out.seek(0)

        return out, new_w, new_h

    except Exception:
        return None, None, None
