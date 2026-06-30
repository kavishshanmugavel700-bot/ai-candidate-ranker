---
title: Redrob Ranker
emoji: ⚡
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# AI Candidate Ranker — RankAI

**Team:** Debug Dynamos
**Hackathon:** RedRob AI Hackathon — India Runs
**Repo:** https://github.com/kavishshanmugavel700-bot/ai-candidate-ranker

An AI-powered recruitment system that ranks candidates against a job description by *understanding* fit — not by keyword matching. The project ships as **two separate systems**:

1. **Interactive Demo** — a recruiter-facing web app (Node.js + Flask + Groq LLM) for live, exploratory JD scoring with comparisons, filters, and exports.
2. **Offline Submission Pipeline** — a fully local, CPU-only script (`generate_submission.py`) that produces the official ranked `team_xxx.csv` per the hackathon's compute and format spec. **No external API calls. No GPU. Under 5 minutes.**

These are intentionally separate. The demo is for showing judges how the product would feel in production; the submission pipeline is what actually gets scored, and it is built to satisfy the hackathon's strict reproducibility constraints (Section 3 of `submission_spec.docx`).

---

## Quick Start — Reproduce the Submission CSV

This is the single command referenced in the hackathon's Stage 3 reproducibility check:

```bash
python generate_submission.py --id YOUR_PARTICIPANT_ID --jd "Paste the released job description here"
```

This produces `YOUR_PARTICIPANT_ID.csv` in the project root with exactly 100 ranked candidates, columns `candidate_id,rank,score,reasoning`.

**Runtime:** ~35-45 seconds on a standard laptop (CPU only, no GPU, no network calls during ranking).
**Memory:** well under 16GB RAM.

---

## Project Structure

```
ai-candidate-ranker/
├── .env                        # API keys (Groq) — NOT committed, demo only
├── .gitignore
├── README.md                   # this file
├── requirements.txt
├── generate_submission.py      # OFFICIAL submission pipeline — zero API calls
│
├── backend/                    # Demo backend (uses Groq — NOT used in submission)
│   ├── jd_extractor.py         # Groq-powered JD requirement extraction
│   ├── scorer.py                # Groq-powered candidate scoring
│   ├── ranker.py                # Combines search + Groq scoring for the demo
│   └── api.py                   # Flask server, POST /rank endpoint (demo only)
│
├── data/                       # Shared by both systems
│   ├── candidates.jsonl         # Full candidate dataset (~100k profiles, not committed — see Dataset section)
│   ├── sample_candidates.json   # Small sample for fast local testing
│   ├── candidate_schema.json    # Field reference for the dataset
│   ├── loader.py                 # Loads & cleans candidates.jsonl
│   ├── preprocess.py             # Converts a candidate record into searchable profile text
│   ├── embedder.py               # sentence-transformers embeddings (cached to disk)
│   └── search.py                 # ChromaDB semantic search (used by the demo backend)
│
├── ui/                          # Demo frontend (Node.js + HTML/CSS/JS)
│   ├── server.js                 # Express server, serves UI + proxies /api to Flask
│   ├── package.json
│   └── public/
│       ├── index.html
│       ├── css/style.css
│       └── js/app.js
│
└── evaluation/                  # Internal testing & comparison tooling
    ├── test_cases.py             # 10 sample JDs used during development
    └── baseline_search.py        # Simple keyword search, used to sanity-check AI ranking quality
```

---

## Two Systems, One Dataset

### 1. Offline Submission Pipeline (`generate_submission.py`)

This is what actually gets scored by the hackathon. It is designed from the ground up to satisfy the constraints in Section 3 of the spec:

| Constraint | How it's satisfied |
|---|---|
| ≤ 5 min runtime | TF-IDF pre-filters the full candidate pool down to the top 1,000 before running embeddings — avoids embedding all ~100k profiles, completing in ~35 seconds. |
| ≤ 16 GB RAM | `sentence-transformers` (`all-MiniLM-L6-v2`) is a small, CPU-friendly model; no large batch held in memory at once |
| CPU only | No `.cuda()` calls anywhere in the pipeline; runs entirely on CPU |
| No network calls | Zero imports of `groq`, `openai`, `anthropic`, or any HTTP client during ranking. `requirements.txt` for this script has no API SDKs |
| Exact CSV format | `candidate_id,rank,score,reasoning`, exactly 100 rows, ranks 1-100 each once, score non-increasing with rank |

**Pipeline steps:**

1. **Load** `data/candidates.jsonl` and filter out detected honeypot profiles (see Honeypot Detection below).
2. **Pre-rank with TF-IDF** — cheap, fast keyword-based similarity narrows the full pool down to the most plausible 1,000 candidates, keeping the expensive embedding step within the time budget.
3. **Score with local embeddings** — `sentence-transformers` encodes the JD and each of the 1,000 candidate profiles; cosine similarity gives a semantic fit score.
4. **Explain** — top 100 by composite score, with a fact-based, template-generated reasoning string for each: cites the candidate's real title, years of experience, matching skills, and companies (no hallucinated claims, no LLM involved).
5. **Score Scaling** — Enforces non-increasing order dynamically scaled between `98.00` and `78.00` to reflect genuine relative confidence.
6. **Write CSV** — `<participant_id>.csv` with the four required columns.

**Honeypot Detection:**

The dataset contains profiles with subtly impossible claims. `generate_submission.py` filters out candidates matching any of:

- A skill marked "expert"/"advanced" proficiency with `duration_months == 0`.
- Career history showing a start date earlier than the employer's known founding year (e.g. a role at Krutrim or Sarvam AI starting before 2023).

This is a best-effort rule-based filter, not exhaustive — the spec notes a well-designed semantic ranker should naturally avoid most honeypots without needing to catch every one.

---

### 2. Interactive Demo (`backend/` + `ui/`)

A separate, fully working web application for live demonstration purposes:

- **Circular AI Radar Loader**: Concentric counter-rotating loader rings synced to live status updates during ranking request processing.
- **Neural Particle Canvas Background**: Performance-optimized constellation background that reacts to mouse cursor movements.
- **3D Perspective Card Tilt**: Hovering candidate cards tilt dynamically in 3D space.
- **Animated Score Tickers**: Numbers count up smoothly from `0` to their final values using eased animation frames.
- **Candidate Side-by-Side Comparison Matrix**: Select up to 3 candidates via checkboxes to generate a comparison grid comparing overall scores, sub-metrics, and AI rationales side-by-side.
- **Interactive Results Toolbar**:
  * **Live Search**: Filter candidates instantly by name or evaluation keywords.
  * **Instant Sorting**: Sort candidates dynamically by overall score, skills, experience, or growth trajectory.
  * **Score Threshold Pills**: Filter matches by score brackets (`All`, `80%+ Match`, `60%+ Match`) without making new backend calls.
- **One-Click Preset Chips**: Ready-to-test sample job descriptions (Backend, Frontend, and Data Science).
- **Spreadsheet & Document Exports**: Download full evaluations and job description metadata directly as Excel (`.xlsx`) spreadsheets or print-ready PDF reports.

**This demo is not used to produce the official submission CSV.** It exists to show how the underlying ranking approach would feel as a real product, and to demonstrate UI/UX thinking beyond the raw ranking algorithm.

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the demo frontend only)
- ~2 GB free disk space for cached embeddings

### Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` includes: `sentence-transformers`, `scikit-learn`, `numpy`, `pandas`, `chromadb`, `flask`, `flask-cors`, `python-dotenv`, `groq` (demo only — not imported by `generate_submission.py`).

### Dataset

Place the hackathon-provided `candidates.jsonl` in `data/candidates.jsonl`. This file is large and is **not committed to the repository** (see `.gitignore`) — it must be sourced from the official hackathon dataset link.

### Environment variables (demo only)

Create a `.env` file in the project root for the demo backend:

```
GROQ_API_KEY=your_groq_api_key_here
```

The offline submission pipeline (`generate_submission.py`) does **not** read or require this file.

---

## Running the Offline Submission Pipeline

```bash
python generate_submission.py --id YOUR_PARTICIPANT_ID --jd "<released job description text>"
```

**Arguments:**

| Flag | Required | Description |
|---|---|---|
| `--id` | Yes | Your team/participant ID — used as the output filename |
| `--jd` | No | Job description text. Defaults to a sample Backend Engineer JD if omitted — always pass the actual released JD for submission |

**Output:** `<participant_id>.csv` in the project root, ready to upload.

### Validating your output locally

Before submitting, verify the CSV satisfies the spec:

```bash
python -c "
import csv
with open('YOUR_PARTICIPANT_ID.csv', newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 100, f'Expected 100 rows, got {len(rows)}'
ranks = [int(r[\"rank\"]) for r in rows]
assert set(ranks) == set(range(1, 101)), 'Ranks must be 1-100, each exactly once'
ids = [r['candidate_id'] for r in rows]
assert len(ids) == len(set(ids)), 'Duplicate candidate_id found'
scores = [float(r['score']) for r in sorted(rows, key=lambda r: int(r['rank']))]
assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1)), 'Scores must be non-increasing with rank'
print('All checks passed.')
"
```

---

## Running the Interactive Demo

The demo requires two servers running simultaneously:

**Terminal 1 — Flask backend:**

```bash
python -m backend.api
```

Runs on `http://localhost:5000`. Exposes `POST /rank`.

**Terminal 2 — Node.js frontend:**

```bash
cd ui
npm install
node server.js
```

Runs on `http://localhost:3000` and proxies `/api/*` requests to the Flask backend.

Open `http://localhost:3000` in a browser, paste a job description, and view ranked results with AI-generated explanations.

---

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │         OFFLINE SUBMISSION           │
                    │     (generate_submission.py)         │
                    │                                       │
  candidates.jsonl ─┼──▶ Honeypot filter                    │
                    │       │                                │
                    │       ▼                                │
                    │  TF-IDF pre-rank (top 1,000)            │
                    │       │                                │
                    │       ▼                                │
                    │  sentence-transformers embeddings       │
                    │       │   (local, CPU-only)              │
                    │       ▼                                │
                    │  Composite score (70% semantic +         │
                    │  30% skill overlap)                      │
                    │       │                                │
                    │       ▼                                │
                    │  Top 100 + fact-based reasoning          │
                    │       │                                │
                    │       ▼                                │
                    │  team_xxx.csv                            │
                    └─────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │          INTERACTIVE DEMO             │
                    │                                       │
  Recruiter ───▶ Node.js UI ───▶ Flask API ───▶ ChromaDB search
  (paste JD)      (port 3000)    (port 5000)        │
                                      │              ▼
                                      ▼        Top candidates
                                 Groq LLM            │
                              (JD parsing +          ▼
                               scoring)         Groq scores +
                                      │          explanations
                                      ▼              │
                              Ranked results ◀────────┘
                              + export (PDF/XLSX)
                                      │
                                      ▼
                                 Displayed in UI
                                 (NOT written to
                                  submission CSV)
```

---

## Team

| Member | Role |
|---|---|
| Vel Adhesh C B | AI Backend & JD Parsing |
| Kavish S | Data & Embeddings |
| Thiakaesh S | Frontend — Node.js + UI |
| Jawahar V | Evaluation & Presentation |

---

## AI Tools Used

Declared per Section 10.4 of the submission spec:

- **Claude** — used throughout development for code review, debugging, architecture discussion, and documentation (including this README).
- **Groq (Llama 3.3 70B)** — used in the interactive demo only, for JD parsing and candidate scoring shown live in the UI. **Not used anywhere in the offline submission pipeline.**

All ranking logic in `generate_submission.py` that produces the official CSV is deterministic, local computation — embeddings + rule-based scoring — with no LLM calls of any kind.

---

## Notes for Reviewers

- The offline submission pipeline and the demo are intentionally decoupled. If you only want to reproduce the scored CSV, you only need `generate_submission.py`, `data/`, and `requirements.txt` — the `backend/` and `ui/` folders are not required.
- The honeypot filter is rule-based and best-effort; it is not the primary defense against honeypots — the semantic + skill-overlap scoring naturally pushes implausible profiles down in rank.
- Score values are scaled to a 78-98 range to reflect genuine relative confidence without producing artificial-looking exact 0 or 100 endpoints. Rank order — not the absolute score value — is what the official metrics (NDCG@10, NDCG@50, MAP, P@10) are computed against.
