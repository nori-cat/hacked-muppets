import cv2
import numpy as np


def analyze_image(filepath):

    img = cv2.imread(filepath)

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