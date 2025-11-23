# util/helpers.py
import base64
from io import BytesIO
from PIL import Image


# ------------------------------------------------------------
# Safe base64 decode
# ------------------------------------------------------------
def safe_b64decode(data_b64: str) -> bytes:
    try:
        return base64.b64decode(data_b64)
    except Exception:
        return b""


# ------------------------------------------------------------
# Resize image (bytes -> PIL -> bytes)
# ------------------------------------------------------------
def image_resize(image_bytes: bytes, max_size: int = 900) -> bytes:
    try:
        # dacă e deja bytes (cum trimite detailed_walkthrough_tab acum)
        if isinstance(b64_data, (bytes, bytearray)):
            img_bytes = b64_data
        else:
            # string base64 clasic
            img_bytes = base64.b64decode(b64_data)

        # resize
        resized = image_resize(img_bytes, max_size=max_size)

        # encode back în base64 text
        return base64.b64encode(resized).decode()
    except Exception:
        # dacă ceva nu merge, întoarce ce a primit (ca să nu crape)
        return b64_data

# ------------------------------------------------------------
# Resize image that is BASE64 encoded
# (used by findings_tab.py)
# ------------------------------------------------------------
def resize_image_b64(b64_data: str, max_size: int = 900) -> str:
    try:
        # decode input
        img_bytes = base64.b64decode(b64_data)

        # resize
        resized = image_resize(img_bytes, max_size=max_size)

        # encode back
        return base64.b64encode(resized).decode()
    except Exception:
        return b64_data
        
        
def format_multiline(text: str) -> str:
    if not text:
        return ""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text.replace("\n", "<br/>")


def preformat(text: str) -> str:
    """Leave formatting EXACTLY as typed (for Preformatted)."""
    if not text:
        return ""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text

def pdf_safe_image(b64: str, max_width_mm=150):
    """
    Converts base64 ? PIL ? scaled ? BytesIO for PDF safe embedding
    """
    try:
        img_data = base64.b64decode(b64)
        img = Image.open(BytesIO(img_data))

        # mm to px conversion – approx 3.78 px per mm
        max_w_px = max_width_mm * 3.78

        w, h = img.size
        scale = min(max_w_px / w, 1)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h))

        out = BytesIO()
        img.save(out, format="PNG")
        out.seek(0)
        return out, new_w, new_h
    except Exception:
        return None, None, None
