from flask import Flask, request
from vision import analyze_image
from classifier import classify_water
from scoring import calculate_score

import os

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

    results = analyze_image(filepath)

    brightness = results["brightness"]
    red = results["red"]
    green = results["green"]
    blue = results["blue"]

    score = calculate_score(
        brightness,
        results["cloudiness"],
        results["edge_count"]
    )

    classification, confidence = classify_water(
        red,
        green,
        blue
    )

    return {
        "message": "Image uploaded",
        "filename": image.filename,
        "height": results["height"],
        "width": results["width"],
        "brightness": brightness,
        "cloudiness": results["cloudiness"],
        "edge_count": results["edge_count"],
        "red": red,
        "green": green,
        "blue": blue,
        "score": score,
        "classification": classification,
        "confidence": confidence
    }


if __name__ == "__main__":
    app.run(debug=True)