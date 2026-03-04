# Sentinel: Security Monitoring & Fraud Detection System

> A unified mini security operations platform that monitors system activity and scores financial transactions for risk.

---

## What Is This?

Sentinel is a dual-module detection system that watches for suspicious behavior across two domains simultaneously:

- **System activity** — failed logins, unusual access times, unknown IPs, suspicious commands
- **Financial transactions** — high-value transfers, rapid repeated payments, location mismatches, new devices

Both modules feed into a **Central Risk Engine** that produces a unified risk score, reason flags, alert level, and incident log for every event.


---

## Core Features

### Intrusion & Activity Detection
Monitors system logs and events for:
- Multiple failed login attempts within a time window
- Access occurring at unusual hours
- Requests from unknown or flagged IP addresses
- Suspicious command patterns in logs

### Transaction Risk Scoring
Analyzes financial events for:
- Unusually high transaction amounts
- Rapid repeated transactions from the same account
- Geographic location mismatches
- Transactions from new or unrecognized devices

### Central Risk Engine
Unifies both modules into a single decision layer that outputs:
- **Risk Score** — weighted numeric score (0–100)
- **Reason Flags** — human-readable list of what triggered the score
- **Alert Level** — LOW / MEDIUM / HIGH / CRITICAL
- **Incident Log** — persistent record of every flagged event

### Alert System
- Console alerts with color-coded severity
- Structured log file output
- Incident storage in SQLite database

---

## Architecture

```
Simulator / Client
        │
        ▼
 Processing Engine
  ├── Activity Detector (log analysis)
  └── Transaction Scorer (fraud rules)
        │
        ▼
  Central Risk Engine
  (unified scoring + reason flags)
        │
        ▼
   SQLite Database
  (incidents + audit trail)
        │
        ▼
  Alert Output
  (console + log file)
```

No message queues. No microservices. No distributed infrastructure. Just a clean, well-structured Python system that does what it says.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| API | FastAPI |
| Database | SQLite (upgradeable to PostgreSQL) |
| Logging | Python `logging` module |
| Testing | pytest |
| Containerization | Docker *(Version 3)* |

---

## Getting Started

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sentinel.git
cd sentinel

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialise the database
python scripts/init_db.py

# Run the simulator to generate test events
python simulator/run.py

# Start the API (optional)
uvicorn app.main:app --reload
```

---

## Project Structure

```
sentinel/
├── app/
│   ├── main.py               # FastAPI entry point
│   ├── models/               # Database models
│   └── routes/               # API endpoints
├── engine/
│   ├── risk_engine.py        # Central Risk Engine
│   ├── activity_detector.py  # Intrusion detection logic
│   └── transaction_scorer.py # Fraud scoring logic
├── simulator/
│   └── run.py                # Generates synthetic events for testing
├── alerts/
│   └── alert_handler.py      # Console + file alert output
├── db/
│   └── incidents.db          # SQLite database
├── logs/
│   └── sentinel.log          # Alert log file
├── tests/
│   └── test_engine.py        # Unit tests
├── scripts/
│   └── init_db.py            # DB setup script
├── requirements.txt
└── README.md
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Risk Scoring Logic

Sentinel uses a **transparent, weighted scoring model** not a black box. Every score comes with a plain-English explanation.

### Activity Score Factors

| Signal | Weight |
|---|---|
| Failed logins > 5 in 10 minutes | +30 |
| Access between 00:00 – 05:00 | +15 |
| IP not in known list | +25 |
| Suspicious command in log | +30 |

### Transaction Score Factors

| Signal | Weight |
|---|---|
| Amount > threshold | +25 |
| 3+ transactions in 60 seconds | +30 |
| Location mismatch from last transaction | +25 |
| New device fingerprint | +20 |

### Alert Levels

| Score Range | Level |
|---|---|
| 0 – 24 | 🟢 LOW |
| 25 – 49 | 🟡 MEDIUM |
| 50 – 74 | 🟠 HIGH |
| 75 – 100 | 🔴 CRITICAL |

---

## Version Roadmap

### Version 1 — Core System *(current)*
- [ ] Rule-based detection for both modules
- [ ] Simulated event input
- [ ] SQLite storage
- [ ] CLI alerts + log file
- [ ] FastAPI interface

### Version 2 — future upgrades
- [ ] Web dashboard (React or simple HTML/JS)
- [ ] Email/SMS alerts via SendGrid or Twilio
- [ ] Basic ML model to replace manual thresholds
- [ ] Apache Kafka as the event pipeline


---

## Design Decisions

**Why rule-based scoring instead of ML?**
Rules are transparent, debuggable, and explainable, which matters in security contexts. Version 2 can introduce a model layer on top of an already-working system rather than replacing one that doesn't exist yet.

**Why SQLite?**
It requires zero infrastructure to run locally, making this genuinely easy to set up and demo. The database layer is abstracted so PostgreSQL is a config change, not a rewrite.

**Why a unified engine?**
A combined risk signal is more actionable than two separate alerts. A user flagged by both the activity detector *and* the transaction scorer simultaneously is a much stronger signal than either alone.

---

## License

MIT — use it, extend it, learn from it.

---

*Built by Keletso Monyamane*
