import cv2
import numpy as np
from PIL import Image

# Large photos are shrunk before analysis: faster, and the
# percentages below don't depend on resolution.
MAX_SIDE = 480


def load_image(filepath):
    img = cv2.imread(filepath)

    if img is None:
        # OpenCV can't decode some formats (e.g. AVIF); try Pillow instead.
        try:
            with Image.open(filepath) as pil:
                rgb = np.array(pil.convert("RGB"))
            img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        except Exception:
            raise ValueError("Could not read that image file")

    return img


def _hue_entropy(hue, saturation):
    """How many different colors are present (rainbow oil sheen = high)."""
    vivid = hue[saturation > 60]
    hist, _ = np.histogram(vivid, bins=18, range=(0, 180))
    total = hist.sum()
    if total == 0:
        return 0.0
    p = hist[hist > 0] / total
    return float(-(p * np.log2(p)).sum())


def _debris_specks(gray):
    """Small high-contrast blobs per 10,000 pixels (bottles, wrappers...)."""
    background = cv2.medianBlur(gray, 21)
    deviation = cv2.absdiff(gray, background)
    mask = (deviation > 45).astype(np.uint8)
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    areas = stats[1:, cv2.CC_STAT_AREA]
    count = int(((areas >= 6) & (areas <= 400)).sum())
    return count / (gray.shape[0] * gray.shape[1] / 10000)


def analyze_image(filepath):

    img = load_image(filepath)

    height, width = img.shape[:2]

    scale = MAX_SIDE / max(height, width)
    if scale < 1:
        img = cv2.resize(
            img,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_AREA,
        )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hue, sat, val = (hsv[..., i].astype(float) for i in range(3))

    colored = sat > 40

    green_frac = ((hue >= 33) & (hue <= 80) & colored).mean()
    blue_frac = ((hue >= 80) & (hue <= 130) & colored).mean()
    brown_frac = ((hue >= 5) & (hue <= 28) & colored & (val < 210)).mean()

    average_color = img.mean(axis=(0, 1))

    return {
        # original fields (the frontend displays these)
        "height": height,
        "width": width,
        "brightness": int(img.mean()),
        "red": int(average_color[2]),
        "green": int(average_color[1]),
        "blue": int(average_color[0]),
        "cloudiness": int(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "edge_count": int(np.count_nonzero(cv2.Canny(gray, 100, 200))),
        # new features used by classifier.py and scoring.py
        "green_frac": round(float(green_frac), 3),
        "blue_frac": round(float(blue_frac), 3),
        "brown_frac": round(float(brown_frac), 3),
        "hue_entropy": round(_hue_entropy(hue, sat), 3),
        "specks": round(float(_debris_specks(gray)), 2),
    }