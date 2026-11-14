import { useEffect, useRef, useState } from 'react'

const CLASSES = {
  clear: {
    label: 'Clear water',
    emoji: '💧',
    tone: 'clear',
    tip: 'No visible contamination. It looks clear, but a photo can’t show chemicals or bacteria.',
  },
  sediment: {
    label: 'Sediment-heavy',
    emoji: '🟤',
    tone: 'sediment',
    tip: 'Silt or soil is clouding the water. Let it settle or filter it before any use.',
  },
  algae: {
    label: 'Algae-contaminated',
    emoji: '🟢',
    tone: 'algae',
    tip: 'Possible algal bloom. Avoid contact and keep pets away until it has been tested.',
  },
  pollution: {
    label: 'Pollution / trash',
    emoji: '🗑️',
    tone: 'pollution',
    tip: 'Floating debris or oil sheen detected. Consider reporting it to local authorities.',
  },
}

const FALLBACK = {
  label: 'Unknown',
  emoji: '❔',
  tone: 'clear',
  tip: 'We couldn’t match this photo to a category.',
}

const HISTORY_KEY = 'aquavision-history'

/* ---------- small helpers ---------- */

function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    let raf
    const start = performance.now()
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3)
      setValue(Math.round(target * eased))
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, duration])
  return value
}

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []
  } catch {
    return []
  }
}

function saveHistory(list) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list))
  } catch {
    /* storage can be blocked, ignore */
  }
}

/* ---------- components ---------- */

function Waves() {
  const d =
    'M0,100 C360,160 360,40 720,100 C1080,160 1080,40 1440,100 C1800,160 1800,40 2160,100 C2520,160 2520,40 2880,100 L2880,200 L0,200 Z'
  return (
    <div className="waves" aria-hidden="true">
      <svg className="wave wave-back" viewBox="0 0 2880 200" preserveAspectRatio="none">
        <path d={d} />
      </svg>
      <svg className="wave wave-front" viewBox="0 0 2880 200" preserveAspectRatio="none">
        <path d={d} />
      </svg>
    </div>
  )
}

function Gauge({ score }) {
  const shown = useCountUp(score)
  const R = 62
  const C = 2 * Math.PI * R
  return (
    <div className="gauge">
      <svg viewBox="0 0 160 160">
        <defs>
          <linearGradient id="gaugeGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#7dd3fc" />
            <stop offset="100%" stopColor="#2563eb" />
          </linearGradient>
        </defs>
        <circle className="gauge-track" cx="80" cy="80" r={R} />
        <circle
          className="gauge-fill"
          cx="80"
          cy="80"
          r={R}
          strokeDasharray={C}
          strokeDashoffset={C * (1 - shown / 100)}
        />
      </svg>
      <div className="gauge-text">
        <span className="gauge-num">{shown}</span>
        <span className="gauge-of">out of 100</span>
      </div>
    </div>
  )
}

function Bar({ label, percent, display }) {
  const p = Math.max(0, Math.min(100, percent))
  return (
    <div className="bar-row">
      <div className="bar-label">
        <span>{label}</span>
        <span>{display ?? `${Math.round(p)}%`}</span>
      </div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${p}%` }} />
      </div>
    </div>
  )
}

/* ---------- main app ---------- */

export default function App() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [scanId, setScanId] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const [history, setHistory] = useState(loadHistory)
  const inputRef = useRef(null)

  // free the preview URL when it changes
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview)
    }
  }, [preview])

  function chooseFile(f) {
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setError('')
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    chooseFile(e.dataTransfer.files?.[0])
  }

  async function analyze() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('image', file)
      const res = await fetch('/upload', { method: 'POST', body: form })
      const data = await res.json().catch(() => ({}))
      if (!res.ok || data.error) {
        throw new Error(data.error || 'The server could not analyze this photo.')
      }
      setResult(data)
      setScanId((n) => n + 1)

      const entry = {
        id: Date.now(),
        filename: data.filename || file.name,
        classification: data.classification,
        score: data.score,
        time: new Date().toLocaleString([], {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        }),
      }
      const next = [entry, ...history].slice(0, 12)
      setHistory(next)
      saveHistory(next)
    } catch (err) {
      setError(
        err instanceof TypeError
          ? 'Can’t reach the server. Is the Flask backend running?'
          : err.message,
      )
    } finally {
      setLoading(false)
    }
  }

  function clearHistory() {
    setHistory([])
    saveHistory([])
  }

  const info = result ? CLASSES[result.classification] || FALLBACK : null

  return (
    <div className="page">
      <Waves />

      <header className="header">
        <div className="logo">💧</div>
        <h1>AquaVision</h1>
        <p>Upload a photo of water and get an instant visual quality report.</p>
      </header>

      <main className="grid">
        {/* ---------- upload card ---------- */}
        <section className="card">
          <h2>Your photo</h2>

          <label
            className={`drop ${dragging ? 'drop-active' : ''} ${preview ? 'drop-has' : ''}`}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              hidden
              onChange={(e) => chooseFile(e.target.files?.[0])}
            />
            {preview ? (
              <img src={preview} alt="Selected water" />
            ) : (
              <div className="drop-empty">
                <div className="drop-icon">🌊</div>
                <strong>Drag &amp; drop a photo</strong>
                <span>or click to browse (JPG, PNG, WEBP, AVIF)</span>
              </div>
            )}
          </label>

          {file && <p className="filename">{file.name}</p>}

          <button className="btn" onClick={analyze} disabled={!file || loading}>
            {loading ? (
              <>
                <span className="spinner" /> Analyzing…
              </>
            ) : (
              'Analyze Water'
            )}
          </button>

          {error && <div className="error">⚠️ {error}</div>}
        </section>

        {/* ---------- results card ---------- */}
        <section className="card">
          <h2>Quality report</h2>

          {!result ? (
            <div className="placeholder">
              <div className="placeholder-icon">🔬</div>
              <p>Your results will appear here after you analyze a photo.</p>
            </div>
          ) : (
            <div className="result fade-in">
              <Gauge key={scanId} score={result.score} />

              <div className={`badge badge-${info.tone}`}>
                <span>{info.emoji}</span> {info.label}
              </div>

              <div className="confidence">
                <Bar label="Confidence" percent={result.confidence} />
              </div>

              <p className="tip">{result.recommendation || info.tip}</p>
            </div>
          )}
        </section>

        {/* ---------- features card ---------- */}
        {result && (
          <section className="card wide fade-in">
            <h2>What the computer vision measured</h2>
            <div className="features">
              <Bar label="Blue / teal coverage" percent={(result.blue_frac ?? 0) * 100} />
              <Bar label="Green coverage" percent={(result.green_frac ?? 0) * 100} />
              <Bar label="Brown coverage" percent={(result.brown_frac ?? 0) * 100} />
              <Bar
                label="Brightness"
                percent={((result.brightness ?? 0) / 255) * 100}
                display={`${Math.round(result.brightness ?? 0)} / 255`}
              />
              <Bar
                label="Colour variety (oil sheen)"
                percent={((result.hue_entropy ?? 0) / 4) * 100}
                display={(result.hue_entropy ?? 0).toFixed(2)}
              />
              <Bar
                label="Floating specks (debris)"
                percent={((result.specks ?? 0) / 10) * 100}
                display={(result.specks ?? 0).toFixed(1)}
              />
            </div>
            {result.width && (
              <p className="meta">
                Analyzed image: {result.width} × {result.height}px
              </p>
            )}
          </section>
        )}

        {/* ---------- history card ---------- */}
        <section className="card wide">
          <div className="card-head">
            <h2>Scan history</h2>
            {history.length > 0 && (
              <button className="link" onClick={clearHistory}>
                Clear
              </button>
            )}
          </div>

          {history.length === 0 ? (
            <p className="muted">No scans yet. Your last 12 scans are saved in this browser.</p>
          ) : (
            <ul className="history">
              {history.map((h) => {
                const c = CLASSES[h.classification] || FALLBACK
                return (
                  <li key={h.id}>
                    <span className="h-emoji">{c.emoji}</span>
                    <div className="h-main">
                      <strong>{c.label}</strong>
                      <span>
                        {h.filename} · {h.time}
                      </span>
                    </div>
                    <span className="h-score">{h.score}</span>
                  </li>
                )
              })}
            </ul>
          )}
        </section>
      </main>

      <footer className="footer">
        A photo only shows what’s visible. AquaVision can’t detect chemical or bacterial
        contamination, so never use it to decide whether water is safe to drink.
      </footer>
    </div>
  )
}