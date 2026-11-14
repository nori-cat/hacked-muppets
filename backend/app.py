from flask import Flask, request
from werkzeug.utils import secure_filename
import uuid
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

    # Sanitize the name (prevents path traversal) and make it unique
    # so uploads never overwrite each other.
    safe_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(image.filename)}"

    filepath = os.path.join(
        UPLOAD_FOLDER,
        safe_name
    )

    image.save(filepath)

    try:
        results = analyze_image(filepath)
    except ValueError as e:
        os.remove(filepath)
        return {"error": str(e)}, 400

    classification, confidence = classify_water(results)

    score = calculate_score(
        classification,
        confidence,
        results
    )

    return {
        "message": "Image uploaded",
        "filename": image.filename,
        "score": score,
        "classification": classification,
        "confidence": confidence,
        **results
    }


if __name__ == "__main__":
    app.run(debug=True)