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

    average_color = img.mean()

    score = int(min(100, average_color / 255 * 100))

    return {
    "message": "Image uploaded",
    "filename": image.filename,
    "score": score,
    "classification": "clear_water"
    }

if __name__ == "__main__":
    app.run(debug=True)