# 💧 AquaVision

Upload a photo of water and get an instant quality report: a score out of 100, a classification, a confidence level, and a recommendation.

AquaVision uses computer vision (OpenCV) to analyze a photo and sort it into one of four categories, with no sensors or special hardware needed.

<!-- Add a screenshot: save it as docs/screenshot.png, then uncomment the next line -->
<!-- ![AquaVision screenshot](docs/screenshot.png) -->

## What it detects

| Classification | What it means |
|---|---|
| ✅ Clear water | Blue or teal water with no visible contamination |
| 🟤 Sediment-heavy | Brown or red water carrying silt or soil |
| 🟢 Algae-contaminated | Green water, a possible algal bloom |
| 🗑️ Pollution / trash | Floating debris or oil sheen |

Each result comes with a **water quality score (0–100)** and a short recommendation.

> **Note:** A photo can only show what's visible. AquaVision can't detect chemical or bacterial contamination, so it should never be used to decide whether water is safe to drink.

## Features

- Drag-and-drop photo upload with preview
- Animated score gauge, classification badge and confidence bar
- Computer vision feature panel (colour coverage, debris, brightness) so you can see what the analysis measured
- Scan history: your last 12 scans are remembered in the browser
- Handles JPG, PNG, WEBP and AVIF; unreadable files return a clear error

## Tech stack

- **Backend:** Python, Flask, OpenCV, NumPy, Pillow
- **Frontend:** React, Vite
- **ML (in progress):** TensorFlow / scikit-learn

## Project structure

```
hacked-muppets/
├── backend/
│   ├── app.py          # Flask API (POST /upload)
│   ├── vision.py       # OpenCV feature extraction
│   ├── classifier.py   # Water classification
│   └── scoring.py      # Quality score
├── frontend/           # React + Vite app
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       └── main.jsx
├── dataset/            # Training images, one folder per class
│   ├── clear/
│   ├── sediment/
│   ├── algae/
│   └── pollution/
├── uploads/            # Saved uploads (git-ignored)
└── requirements.txt
```

## Getting started

### Requirements

- Python 3.10 or newer
- Node.js 18 or newer

### 1. Backend

From the repo root:

```bash
python -m venv venv

# Windows PowerShell
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python backend/app.py
```

The API runs at `http://127.0.0.1:5000`. Run it from the repo root so `uploads/` is created in the right place. Leave it running.

> `requirements.txt` includes TensorFlow, so the first install can take several minutes.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the link Vite prints (usually `http://localhost:5173`). The dev server forwards `/upload` to Flask, so no extra setup is needed.

**Windows note:** if PowerShell says "running scripts is disabled", run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 3. Try it

Drag a photo from `dataset/` onto the page and click **Analyze Water**.

## How it works

1. **Upload:** the React app sends the photo to Flask (`POST /upload`, form field `image`).
2. **Feature extraction (`vision.py`):** the image is shrunk to 480px and converted to HSV colour space. OpenCV measures:
   - the share of green, blue and brown pixels
   - colour variety (rainbow oil sheen scores high)
   - small high-contrast "specks" that suggest floating debris
   - brightness and average colour
3. **Classification (`classifier.py`):** rules based on those features pick the category and a confidence value.
4. **Scoring (`scoring.py`):** each category has its own score band, so a label and its score always agree. Within a band, the score reflects how much of the image shows the problem.
5. **Report:** the frontend displays the result and saves it to the scan history.

## API

`POST /upload`, multipart form with an `image` file.

Example response (shortened):

```json
{
  "filename": "aw2.jpeg",
  "classification": "algae",
  "confidence": 90,
  "score": 27,
  "green_frac": 0.67,
  "blue_frac": 0.33,
  "brown_frac": 0.0,
  "hue_entropy": 2.36,
  "specks": 2.7,
  "brightness": 134,
  "width": 1024,
  "height": 768
}
```

Errors return `{"error": "..."}` with status 400.

## Known limitations

- The classifier is **rule-based** and its thresholds were tuned on a very small dataset (12 images), so real-world accuracy will be lower than it looks on our own images.
- Scene content such as rocks, sky, trees or hands can confuse colour-based rules.
- Floating trash on brown water can be classified as sediment.
- The score estimates visible condition only, not safety.

## Roadmap

- [ ] Grow the dataset to 15+ photos per class
- [ ] Replace the rules with a machine learning classifier (pretrained image features plus a small trained model), keeping the rules as a fallback
- [ ] Evaluate on photos the model has never seen
- [ ] Map view and a saved scan database
- [ ] Hardware sensor integration (stretch goal)

## Team

Built for a hackathon by the hacked-muppets team.
