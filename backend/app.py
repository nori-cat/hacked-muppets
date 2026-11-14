from flask import Flask, request
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

    filepath = os.path.join(
        UPLOAD_FOLDER,
        image.filename
    )

    image.save(filepath)

    return {
        "message": "Image uploaded",
        "filename": image.filename
    }

if __name__ == "__main__":
    app.run(debug=True)