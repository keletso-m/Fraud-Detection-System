# 🛡 Sentinel
**Security Monitoring & Fraud Detection System**

Built by Keletso Monyamane · MIT License · Python 3.11+ · FastAPI · SQLite

---

## What Is Sentinel?

Sentinel is a dual-module detection system that watches for suspicious behaviour across two domains simultaneously — system activity and financial transactions. Both modules feed into a Central Risk Engine that produces a unified risk score (0–100), alert level, reason flags, and a persistent incident log for every event.

---

## Features Complete (v1 — current branch)

| Feature | Status | How to verify |
|---|---|---|
| Activity Detector | Done | `python simulator/run.py` |
| Transaction Scorer | Done | `python simulator/run.py` |
| Central Risk Engine | Done | `python simulator/run.py` |
| Alert Handler (console + log) | Done | Check `logs/sentinel.log` after simulator |
| SQLite persistence | Done | `python simulator/run.py` then check `db/incidents.db` |
| Unit tests (39 tests) | Done | `pytest tests/ -v` |
| FastAPI routes | Done | `uvicorn app.main:app --reload` → visit `/docs` |

---

## 🚀 Quickstart — run it in 4 steps

```bash
# 1. Clone and create virtual environment
git clone https://github.com/yourusername/sentinel.git
cd sentinel
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialise the database
python scripts/init_db.py

# 4. Run the simulator — fires 5 test scenarios through the full pipeline
python simulator/run.py
```

You should see 5 colour-coded alerts in your terminal (🟢 LOW → 🔴 CRITICAL) and a `logs/sentinel.log` file with the full NDJSON record.

---

## 🧪 Run the tests

```bash
pytest tests/ -v
```

Expected output: **39 passed, 0 failed**

Tests cover:
- All 4 activity detection signals with boundary cases
- All 4 transaction fraud signals with boundary cases
- Risk engine score blending and alert level assignment
- Combined signal (both detectors fire simultaneously)
- Full pipeline integration test (no database required)

---

## 🌐 API

```bash
uvicorn app.main:app --reload
```

Then open **http://localhost:8000/docs** for the interactive API explorer.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Service status |
| GET | `/health` | Liveness check |
| POST | `/events/activity` | Submit a system activity event |
| POST | `/events/transaction` | Submit a transaction event |
| GET | `/incidents` | List all incidents |
| GET | `/incidents/{id}` | Get one incident by ID |

---

## 📁 Project Structure

```
sentinel/
├── app/
│   ├── main.py                   # FastAPI entry point
│   └── routes/
│       ├── activity.py           # POST /events/activity
│       ├── transactions.py       # POST /events/transaction
│       └── incidents.py          # GET  /incidents
├── engine/
│   ├── activity_detector.py      # Intrusion detection logic
│   ├── risk_engine.py            # Central risk scoring + DB writes
│   └── transaction_scorer.py     # Fraud scoring logic
├── alerts/
│   └── alert_handler.py          # Console + rotating log file output
├── simulator/
│   └── run.py                    # Generates 5 synthetic test scenarios
├── scripts/
│   └── init_db.py                # Database initialiser (safe to re-run)
├── tests/
│   └── test_engine.py            # 39 unit + integration tests
├── db/
│   └── incidents.db              # SQLite — auto-created on first run
├── logs/
│   └── sentinel.log              # NDJSON alert log — auto-created on first run
├── requirements.txt
└── README.md
```

---

## ⚙️ Risk Scoring

Sentinel uses a transparent, weighted model — not a black box. Every score comes with plain-English reason flags.

**Activity signals**

| Signal | Weight |
|---|---|
| Failed logins > 5 in 10 min | +30 |
| Access between 00:00–05:00 UTC | +15 |
| IP not in known allowlist | +25 |
| Suspicious command in log | +30 |

**Transaction signals**

| Signal | Weight |
|---|---|
| Amount > ZAR 10 000 | +25 |
| 3+ transactions in 60 seconds | +30 |
| Location mismatch from last transaction | +25 |
| New / unrecognised device | +20 |

**Alert levels**

| Score | Level |
|---|---|
| 0–24 | 🟢 LOW |
| 25–49 | 🟡 MEDIUM |
| 50–74 | 🟠 HIGH |
| 75–100 | 🔴 CRITICAL |

---

## 🗺 Roadmap

**v1 — Core System (current)**
- [x] Rule-based detection for both modules
- [x] Simulated event input (5 scenarios)
- [x] SQLite storage with rotating log file
- [x] CLI alerts + NDJSON log file
- [x] FastAPI interface with Pydantic validation
- [x] 39 unit and integration tests

**v2 — Planned**
- [ ] Web dashboard (React or plain HTML/JS)
- [ ] Email / SMS alerts via SendGrid or Twilio
- [ ] ML scoring layer on top of existing rules
- [ ] Apache Kafka as the event pipeline
- [ ] PostgreSQL upgrade (config change only)

---

## 🔧 Design Decisions

**Why rule-based scoring instead of ML?** Rules are transparent, debuggable, and explainable — which matters in security. A model layer can be added in v2 on top of a working system rather than replacing one that doesn't exist yet.

**Why SQLite?** Zero infrastructure to run locally. The DB layer is abstracted so PostgreSQL is a config change, not a rewrite.

**Why a unified risk engine?** A combined signal is more actionable than two separate alerts. A user flagged by both detectors simultaneously is a much stronger signal than either alone.

---

## License

MIT — use it, extend it, learn from it.

---

*Built by Keletso Monyamane*
