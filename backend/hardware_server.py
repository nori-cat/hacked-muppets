"""Reads the Pico's JSON lines over USB serial and serves them on the web.

Run:   pip install flask pyserial
       python server.py
Open:  http://<this-computer's-ip>:5000/        (page)
       http://<this-computer's-ip>:5000/api/water   (JSON)

Optional env vars: WATER_PORT (e.g. COM5 or /dev/ttyACM0), WATER_PORT_NUM (web port),
                   STALE_AFTER_S (seconds before data is flagged stale, default 5)
"""
import json
import os
import threading
import time

import serial
import serial.tools.list_ports
from flask import Flask, jsonify, request

BAUD = 115200
WEB_PORT = int(os.environ.get("WATER_PORT_NUM", "5000"))
STALE_AFTER_S = float(os.environ.get("STALE_AFTER_S", "5"))
REQUIRED = ("status", "temp_c", "ppm", "turbidity_pct")

app = Flask(__name__)
_lock = threading.Lock()
_latest = None  # last good reading + the time we received it


def find_port():
    forced = os.environ.get("WATER_PORT")
    if forced:
        return forced
    ports = list(serial.tools.list_ports.comports())
    for p in ports:                      # Raspberry Pi vendor ID
        if p.vid == 0x2E8A:
            return p.device
    for p in ports:                      # fallback: common USB serial names
        if any(k in p.device for k in ("ttyACM", "usbmodem", "COM")):
            return p.device
    return None


def reader_loop():
    """Read forever; reconnect if the Pico is unplugged. Ignores any line that
    isn't a full reading (boot/event messages, partial lines, garbage)."""
    global _latest
    while True:
        port = find_port()
        if not port:
            time.sleep(2)
            continue
        try:
            with serial.Serial(port, BAUD, timeout=2) as ser:
                print("Listening on", port)
                while True:
                    raw_line = ser.readline()
                    if not raw_line:
                        continue
                    try:
                        data = json.loads(raw_line.decode("utf-8", "ignore").strip())
                    except ValueError:
                        continue
                    if not isinstance(data, dict) or not all(k in data for k in REQUIRED):
                        continue
                    data["_received"] = time.time()
                    with _lock:
                        _latest = data
        except (serial.SerialException, OSError) as e:
            print("Serial error:", e, "- retrying")
            time.sleep(2)


def snapshot(include_raw=False):
    with _lock:
        d = dict(_latest) if _latest else None
    if d is None:
        return None
    age = time.time() - d.pop("_received")
    out = {
        "status": d["status"],
        "temp_c": d["temp_c"],
        "ppm": d["ppm"],
        "turbidity_pct": d["turbidity_pct"],
        "age_s": round(age, 1),
        "stale": age > STALE_AFTER_S,
    }
    if include_raw and "raw" in d:
        out["raw"] = d["raw"]
    return out


@app.route("/api/water")
def api_water():
    snap = snapshot(include_raw=request.args.get("raw") == "1")
    if snap is None:
        return jsonify({"error": "no data received yet"}), 503
    return jsonify(snap)


# claude slop for title card. not necessarily harmful so it can stay i guess.
PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Water Quality</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;padding:24px;background:#0f1720;color:#e8eef5}
 .status{font-size:2rem;font-weight:700;padding:16px;border-radius:12px;text-align:center;margin-bottom:16px}
 .ok{background:#1f7a3f}.warn{background:#b7791f}.bad{background:#c53030}.off{background:#4a5568}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
 .card{background:#1a2532;border-radius:12px;padding:16px;text-align:center}
 .v{font-size:2rem;font-weight:700}.l{opacity:.7;font-size:.85rem}
 #note{margin-top:16px;text-align:center;opacity:.7;font-size:.85rem}
</style></head><body>
<div id="status" class="status off">Waiting for data…</div>
<div class="grid">
 <div class="card"><div class="v" id="temp">–</div><div class="l">Temperature (°C)</div></div>
 <div class="card"><div class="v" id="ppm">–</div><div class="l">PPM</div></div>
 <div class="card"><div class="v" id="turb">–</div><div class="l">Turbidity (%)</div></div>
</div>
<div id="note"></div>
<script>
async function tick(){
  const s=document.getElementById('status'),n=document.getElementById('note');
  try{
    const r=await fetch('/api/water'); if(!r.ok) throw 0; const d=await r.json();
    s.textContent=d.status;
    s.className='status '+(d.status.startsWith('CLEAN')?'ok':d.status.startsWith('MODERATE')?'warn':d.status.startsWith('CONTAM')?'bad':'off');
    temp.textContent=d.temp_c; ppm.textContent=d.ppm; turb.textContent=d.turbidity_pct;
    n.textContent=d.stale?'⚠ Data is stale ('+d.age_s+'s old): is the sensor connected?':'';
  }catch(e){ s.textContent='No data'; s.className='status off'; }
}
tick(); setInterval(tick,2000);
</script></body></html>"""


@app.route("/")
def index():
    return PAGE


if __name__ == "__main__":
    threading.Thread(target=reader_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=WEB_PORT)
