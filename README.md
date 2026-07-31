# 🏥 Personal Health AI Dashboard

A full-stack personal health analytics platform built on **Medallion Architecture** (Bronze → Silver → Gold), processing 5 years of Samsung Health device data and Danish healthcare records (Sundhedsplatformen) into an interactive AI-powered dashboard.

> Built as a personal project to explore what 5 years of your own health data actually looks like — and to ask it questions.

---

## ✨ Features

- **Medallion Architecture** data pipeline with Bronze, Silver and Gold layers
- **AI chat assistant** powered by Gemini 2.5 Flash with full health context injected
- **Interactive time-series charts** for sleep, steps, heart rate, stress, blood oxygen and wellness score
- **7-day rolling averages** and trend slopes pre-computed in the Gold layer
- **Cross-domain analysis** — e.g. sleep quality vs next-day activity
- **Composite wellness score** derived from sleep, activity, heart rate and stress
- **Lab results table** with normal/abnormal highlighting
- **Full-text search** across the Silver layer
- **Auto-trigger ETL** when new data files are added via the file watcher, or when the Android app syncs Health Connect data
- **Automated Samsung Health sync** via a companion Android app reading Health Connect (no manual CSV export needed for steps, heart rate, sleep, blood oxygen, calories)
- Accessible from **any device** on your local network

---

## 🏗️ Architecture

```
DATA/
├── samsung/        Raw Samsung Health CSV exports
└── sundhed/        Danish healthcare records (Sundhedsplatformen)

bronze/             Raw parquet files — one per source, no transformations
silver/             Cleaned & normalised domain tables
gold/               Aggregated, analytics-ready tables
static/
└── index.html      Single-page web dashboard
etl.py              Bronze → Silver → Gold pipeline
main.py             FastAPI backend
scheduler.py        File watcher — re-runs ETL on new data
```

### Bronze Layer
- Ingests all 12 source files as-is into parquet format
- Adds `_ingestion_timestamp` and `_source_filename` metadata columns
- Handles encoding quirks (BOM, Danish date formats, US date formats)

### Silver Layer
Produces 10 clean domain tables:

| Table | Source |
|---|---|
| `sleep` | Samsung Health sleep tracking |
| `heart_rate` | Samsung Health heart rate (4-hourly) |
| `activity` | Samsung Health daily steps |
| `blood_oxygen` | Samsung Health SpO₂ |
| `stress` | Samsung Health stress (30-min windows) |
| `calories` | Samsung Health calories burned |
| `lab_results` | Sundhed lab results + prøvesvar |
| `hospital_visits` | Sundhed hospital visits |
| `diagnoses` | Sundhed diagnoses + ICD codes |
| `vaccinations` | Sundhed vaccination records |

### Gold Layer
Produces 11 analytics-ready tables:

| Table | Description |
|---|---|
| `sleep_gold` | Daily sleep with 7-day rolling averages, REM%, deep% |
| `activity_gold` | Daily steps, rolling avg, personal record, 30-day trend slope |
| `heart_rate_gold` | Daily mean/min/max, resting HR (03:00–06:00 UTC), rolling avg |
| `blood_oxygen_gold` | Daily SpO₂, low-oxygen flags |
| `stress_gold` | Daily mean/max stress, rolling avg, high-stress flags |
| `wellness_score` | Composite 0–100 score from sleep + steps + HR + stress |
| `lab_results_gold` | Latest value per test with abnormal flags |
| `cross_domain_sleep_activity` | Sleep quality day N vs steps day N+1 |
| `daily_summary` | All domains joined on date |
| `weekly_summary` | Week-level aggregations |
| `monthly_summary` | Month-level aggregations |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Data processing | Python, pandas, pyarrow |
| API backend | FastAPI, uvicorn |
| AI chat | Google Gemini 2.5 Flash (REST API) |
| Frontend | Vanilla JS, Chart.js 4.x |
| File watching | Watchdog |
| Data format | Parquet (Apache Arrow) |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- A Google AI Studio API key ([get one here](https://aistudio.google.com))
- Samsung Health data export (optional — mock data included)

### Installation

```bash
# Clone the repository
git clone https://github.com/maliksp-ai/health-dashboard.git
cd health-dashboard

# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here

# Optional: required by the /ingest/health_connect endpoint if set.
# Leave unset for LAN-only use; set it if the port is reachable beyond your LAN.
HEALTH_CONNECT_SYNC_TOKEN=
```

### Add your data

Place your Samsung Health CSV exports in `DATA/samsung/` and any Sundhedsplatformen exports in `DATA/sundhed/`.

Expected Samsung Health files:
```
com.samsung.health.sleep.csv
com.samsung.health.heart_rate.csv
com.samsung.health.step_daily_trend.csv
com.samsung.health.blood_oxygen.csv
com.samsung.health.stress.csv
com.samsung.health.calories_burned.csv
```

### Run the ETL pipeline

```bash
python etl.py
```

This will create all Bronze, Silver and Gold parquet files.

### Start the dashboard

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Open **http://localhost:8080** in your browser.

To access from your phone, find your PC's local IP:
```bash
# Windows
ipconfig | findstr "IPv4"
```
Then open `http://YOUR_LOCAL_IP:8080` on your phone (same WiFi network).

### Run the file watcher (optional)

Automatically re-runs ETL when new files are added to `DATA/`:

```bash
python scheduler.py
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serve the dashboard |
| GET | `/health` | API status and available tables |
| GET | `/gold/{domain}` | Gold layer data (supports `limit`, `start_date`, `end_date`) |
| GET | `/silver/search?q=` | Full-text search across Silver layer |
| GET | `/summary` | Compact health summary for AI context |
| POST | `/chat` | Multi-turn AI chat with health context |
| POST | `/etl/run` | Trigger ETL pipeline from the browser |
| POST | `/ingest/health_connect` | Ingest a batch of records synced from the Android Health Connect app (see below) |

---

## 💬 AI Chat

The AI assistant has access to a compact summary of your Gold layer data — including 7 and 30-day averages, lab highlights, diagnoses and wellness trend. Example questions:

- *"Has my resting heart rate decreased over time?"*
- *"What is my average sleep in 2024?"*
- *"Which days am I most active?"*
- *"What do my lab results show?"*
- *"When have I had high stress levels?"*

---

## 📱 Samsung Health sync via Health Connect (automated, no manual export)

Samsung has no public cloud API that a server can call to fetch your personal
Samsung Health data. The only supported way to pull it programmatically is
**Health Connect** — Android's on-device health data broker, which Samsung
Health can write into. `android/HealthConnectSync/` is a small companion app
that reads your data out of Health Connect and pushes it straight into the
Bronze layer via a new endpoint, so you don't have to manually export/import
CSVs every time.

```
android/HealthConnectSync/     Android Studio project (Kotlin)
├── app/.../HealthConnectManager.kt   Reads Steps/HeartRate/Sleep/SpO2/ActiveCalories
├── app/.../SyncUploader.kt           POSTs JSON to /ingest/health_connect
└── app/.../MainActivity.kt           Permission grant + "Sync now" button
```

**How it fits the pipeline:** the app shapes each domain into the same
column names the Samsung CSV bronze tables already use, and the backend
writes them to `bronze/healthconnect_<domain>.parquet`. `etl.py`'s Silver
transforms concatenate `samsung_*` and `healthconnect_*` bronze sources
before continuing, so Gold tables and the dashboard need no changes —
both sources just merge.

### Setup

1. **Enable the Samsung Health ↔ Health Connect sync** on your phone: Samsung
   Health app → Settings → *Sync with Health Connect* → turn on the data
   types you want synced (steps, heart rate, sleep, blood oxygen, active
   calories). Samsung Health only writes into Health Connect for the types
   you enable here.
2. **Build the app**: open `android/HealthConnectSync/` in Android Studio,
   let Gradle sync, connect your phone (or build a release APK and sideload
   it), and run it. `minSdk` is 26; if the Health Connect app itself isn't
   preinstalled (Android 13 and below), the app will offer to open it on the
   Play Store.
3. **Grant permissions**: tap *Grant Health Connect permissions* in the app,
   allow the requested data types in the system dialog.
4. **Point it at your dashboard**: enter your PC's local IP and port (e.g.
   `http://192.168.1.100:8000`) in the *Server URL* field — same address
   used to reach the dashboard from your phone. If you set
   `HEALTH_CONNECT_SYNC_TOKEN` in `.env` (recommended if the port is
   reachable beyond your own LAN), enter the same value in *Sync token*.
5. **Tap "Sync now"**. The app reads everything since its last successful
   sync (30 days on first run), POSTs it to `/ingest/health_connect`, and the
   backend re-runs the ETL pipeline in the background automatically.

### Limitations

- **No stress data.** Health Connect has no "stress" record type, so
  Samsung Health's stress metric cannot be synced this way — it still needs
  the manual CSV export (`DATA/samsung/com.samsung.health.stress.csv`).
- **No automatic background sync.** This is a foreground "sync now" app, not
  a background service — Health Connect access from a background service
  requires more Android plumbing (foreground service + battery-optimization
  exemptions) that wasn't worth the complexity for a personal project. Open
  the app and tap sync whenever you want fresh data.
- Only synced from the moment you enable each data type in Samsung Health's
  Health Connect settings — it won't backfill years of history the way a
  full CSV export does.

---

## 📊 Data Sources

### Samsung Health
Exported directly from the Samsung Health app (Profile → Settings → Data privacy → Download personal data), or synced automatically via the Health Connect companion app above. Covers sleep, heart rate, steps, blood oxygen, stress (CSV export only) and calories.

### Sundhedsplatformen (Denmark)
Danish national health platform records including lab results, hospital visits, diagnoses and vaccinations. Accessed via personal data export — all within legal boundaries under GDPR Article 20 (right to data portability).

---

## 🔒 Privacy & Security

- Your `.env` file (API key) is excluded from git via `.gitignore`
- Your raw health data in `DATA/` is excluded from git
- Your generated parquet files in `bronze/`, `silver/` and `gold/` are excluded from git
- Only code is committed — never personal data

---

## 📁 Project Structure

```
health-dashboard/
├── DATA/
│   ├── samsung/                    Samsung Health CSV exports
│   └── sundhed/                    Danish healthcare records
├── bronze/                         Raw parquet files (git-ignored)
├── silver/                         Clean domain tables (git-ignored)
├── gold/                           Analytics tables (git-ignored)
├── android/
│   └── HealthConnectSync/          Android app: syncs Samsung Health data via Health Connect
├── static/
│   └── index.html                  Web dashboard
├── etl.py                          Medallion ETL pipeline
├── main.py                         FastAPI backend + AI chat + Health Connect ingestion
├── scheduler.py                    File watcher
├── generate_mock_data.py           Generate 5 years of mock Samsung data
├── requirements.txt                Python dependencies
└── .env                            API keys (git-ignored)
```

---

## 🙏 Acknowledgements

A special thank you to **Claus** for countless conversations about AI, technology and what it all actually means. Those talks shaped this project more than any tutorial ever could.

Built with the help of **Claude Code** by Anthropic.

---

## 📄 License

MIT License — feel free to use, modify and build on this project.
