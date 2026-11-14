import cv2
import numpy as np
from PIL import Image


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


def analyze_image(filepath):

    img = load_image(filepath)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    height, width, channels = img.shape

    brightness = int(img.mean())

    average_color = img.mean(axis=(0, 1))

    blue = int(average_color[0])
    green = int(average_color[1])
    red = int(average_color[2])

    cloudiness = int(
        cv2.Laplacian(gray, cv2.CV_64F).var()
    )

    edges = cv2.Canny(gray, 100, 200)

    edge_count = int(np.count_nonzero(edges))

    return {
        "height": height,
        "width": width,
        "brightness": brightness,
        "red": red,
        "green": green,
        "blue": blue,
        "cloudiness": cloudiness,
        "edge_count": edge_count
    }