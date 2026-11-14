from flask import Flask, request
import os
import cv2
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return """
    <h1>AquaVision</h1>

    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="image">
        <button type="submit">Upload</button>
    </form>
    """

@app.route("/upload", methods=["POST"])
def upload():

    if "image" not in request.files:
        return {"error": "No image uploaded"}, 400

    image = request.files["image"]
    if not image.filename.lower().endswith(
    (".png", ".jpg", ".jpeg", ".webp", ".avif")
    ):
        return {
        "error": "Please upload an image file"
        }, 400

    filepath = os.path.join(
        UPLOAD_FOLDER,
        image.filename
    )

    image.save(filepath)
    
    img = cv2.imread(filepath)
    
    height, width, channels = img.shape
    
    average_brightness = int(img.mean())
    average_color = img.mean(axis=(0, 1))
    
    blue = int(average_color[0])
    green = int(average_color[1])
    red = int(average_color[2])

    score = int(min(100, average_brightness / 255 * 100))
    
    if green > red + 15:
        classification = "algae"

    elif red > blue + 15:
        classification = "sediment"

    else:
        classification = "clear_water"

    return {
    "message": "Image uploaded",
    "filename": image.filename,
    "height": height,
    "width": width,
    "brightness": average_brightness,
    "red": red,
    "green": green,
    "blue": blue,
    "score": score,
    "classification": classification
    }

if __name__ == "__main__":
    app.run(debug=True)