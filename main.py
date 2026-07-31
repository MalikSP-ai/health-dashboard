"""
FastAPI backend for Personal Health AI Dashboard
Serves Bronze/Silver/Gold layer data and Gemini AI chat
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import requests as _requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

# --- Gemini REST API (works on Python 3.8 without google-generativeai) ---
_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
_GEMINI_OK = bool(_GEMINI_API_KEY)

def _gemini_chat(contents: list, system_instruction: str = "") -> str:
    """Call Gemini REST API and return the text reply."""
    payload: Dict[str, Any] = {"contents": contents}
    if system_instruction:
        payload["system_instruction"] = {"parts": [{"text": system_instruction}]}
    r = _requests.post(
        _GEMINI_BASE,
        params={"key": _GEMINI_API_KEY},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
BRONZE_DIR = BASE_DIR / "bronze"
GOLD_DIR = BASE_DIR / "gold"
SILVER_DIR = BASE_DIR / "silver"
STATIC_DIR = BASE_DIR / "static"

_HEALTH_CONNECT_SYNC_TOKEN = os.environ.get("HEALTH_CONNECT_SYNC_TOKEN", "")

app = FastAPI(title="Health Dashboard API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _df_to_records(df: pd.DataFrame) -> List[dict]:
    """Convert DataFrame to JSON-safe list of dicts."""
    if df.empty:
        return []
    # Convert timestamps and handle NaN
    out = json.loads(
        df.to_json(orient="records", date_format="iso", default_handler=str, force_ascii=False)
    )
    # Replace None/NaN sentinel strings
    def clean(v: Any) -> Any:
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return None
        return v

    return [{k: clean(v) for k, v in row.items()} for row in out]


def _read_gold(name: str) -> pd.DataFrame:
    path = GOLD_DIR / f"{name}.parquet"
    if not path.exists():
        raise HTTPException(404, f"Gold table '{name}' not found. Run ETL first.")
    return pd.read_parquet(path)


def _read_silver(name: str) -> pd.DataFrame:
    path = SILVER_DIR / f"{name}.parquet"
    if not path.exists():
        raise HTTPException(404, f"Silver table '{name}' not found. Run ETL first.")
    return pd.read_parquet(path)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def serve_dashboard():
    index = STATIC_DIR / "index.html"
    if not index.exists():
        return {"message": "Dashboard not found. Place static/index.html in the project."}
    return FileResponse(str(index))


@app.get("/health")
def health_check():
    gold_tables = [f.stem for f in GOLD_DIR.glob("*.parquet")] if GOLD_DIR.exists() else []
    silver_tables = [f.stem for f in SILVER_DIR.glob("*.parquet")] if SILVER_DIR.exists() else []
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gold_tables": sorted(gold_tables),
        "silver_tables": sorted(silver_tables),
        "gemini_available": _GEMINI_OK,
    }


@app.get("/gold/{domain}")
def get_gold_domain(
    domain: str,
    limit: int = 730,
    start_date: str = None,
    end_date: str = None,
):
    df = _read_gold(domain)
    if df.empty:
        return []

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if start_date:
            df = df[df["date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["date"] <= pd.to_datetime(end_date)]
        df = df.sort_values("date").tail(limit)

    return _df_to_records(df)


@app.get("/gold")
def list_gold_tables():
    if not GOLD_DIR.exists():
        return {"tables": []}
    return {"tables": sorted(f.stem for f in GOLD_DIR.glob("*.parquet"))}


@app.get("/silver/search")
def search_silver(q: str, domain: str = None, limit: int = 100):
    if not q or len(q.strip()) < 2:
        raise HTTPException(400, "Query must be at least 2 characters")

    targets = [domain] if domain else [
        f.stem for f in SILVER_DIR.glob("*.parquet")
    ] if SILVER_DIR.exists() else []

    results = []
    for table in targets:
        path = SILVER_DIR / f"{table}.parquet"
        if not path.exists():
            continue
        try:
            df = pd.read_parquet(path)
            mask = df.apply(
                lambda col: col.astype(str).str.contains(q, case=False, na=False)
            ).any(axis=1)
            hits = df[mask].head(limit).copy()
            hits["_silver_table"] = table
            results.append(hits)
        except Exception as e:
            log.error(f"Search failed for {table}: {e}")

    if not results:
        return {"results": [], "count": 0, "query": q}

    combined = pd.concat(results, ignore_index=True).head(limit)
    return {"results": _df_to_records(combined), "count": len(combined), "query": q}


@app.get("/summary")
def get_summary():
    """Compact health summary for AI context injection (~2000 tokens)."""
    summary: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_range": {},
        "recent_30d": {},
        "recent_7d": {},
        "lab_highlights": [],
        "diagnoses": [],
        "wellness_trend": [],
        "vaccinations": [],
    }

    # --- Data range from daily_summary ---
    try:
        ds = _read_gold("daily_summary")
        if not ds.empty and "date" in ds.columns:
            ds["date"] = pd.to_datetime(ds["date"])
            summary["data_range"] = {
                "start": ds["date"].min().date().isoformat(),
                "end": ds["date"].max().date().isoformat(),
                "total_days": int(ds["date"].nunique()),
            }
            # Last 30 days averages
            cutoff_30 = ds["date"].max() - pd.Timedelta(days=30)
            cutoff_7 = ds["date"].max() - pd.Timedelta(days=7)
            recent_30 = ds[ds["date"] >= cutoff_30].select_dtypes(include="number").mean().round(1)
            recent_7 = ds[ds["date"] >= cutoff_7].select_dtypes(include="number").mean().round(1)
            summary["recent_30d"] = {k: (None if pd.isna(v) else v) for k, v in recent_30.items()}
            summary["recent_7d"] = {k: (None if pd.isna(v) else v) for k, v in recent_7.items()}
    except Exception:
        pass

    # --- Lab highlights ---
    try:
        labs = _read_gold("lab_results_gold")
        if not labs.empty:
            highlights = labs[["test_name", "value", "unit", "abnormal", "date"]].copy()
            highlights = highlights.fillna("")
            summary["lab_highlights"] = _df_to_records(highlights.head(30))
    except Exception:
        pass

    # --- Diagnoses ---
    try:
        diag = _read_silver("diagnoses")
        if not diag.empty:
            summary["diagnoses"] = _df_to_records(diag[["diagnosis", "icd_code", "date"]].head(20))
    except Exception:
        pass

    # --- Wellness trend (last 30 days) ---
    try:
        ws = _read_gold("wellness_score")
        if not ws.empty and "date" in ws.columns:
            ws["date"] = pd.to_datetime(ws["date"])
            recent = ws.sort_values("date").tail(30)
            summary["wellness_trend"] = _df_to_records(
                recent[["date", "wellness_score"]].dropna()
            )
    except Exception:
        pass

    # --- Vaccinations ---
    try:
        vacc = _read_silver("vaccinations")
        if not vacc.empty:
            summary["vaccinations"] = _df_to_records(vacc.head(10))
    except Exception:
        pass

    return summary


# ---------------------------------------------------------------------------
# AI Chat
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a personal health assistant. You analyse the user's own health data and answer questions in a friendly, fact-based and easy-to-understand way.

Rules:
- Reply in English by default; switch to Danish if the user writes in Danish
- You are NOT a doctor — make this clear if the user asks medical questions
- Use concrete numbers from the provided data whenever possible
- Keep answers concise and accurate
- Format numbers nicely (e.g. "7,234 steps" not "7234.0")"""


class ChatRequest(BaseModel):
    message: str
    include_context: bool = True
    conversation_history: List[dict] = []


@app.post("/chat")
async def chat(req: ChatRequest):
    if not _GEMINI_OK:
        raise HTTPException(503, "Gemini AI not available. Check GEMINI_API_KEY in .env")

    try:
        # Build contents array for Gemini REST API multi-turn format
        contents = []

        # Replay existing conversation history
        for turn in req.conversation_history:
            role = turn.get("role", "user")
            parts = turn.get("parts", [])
            if isinstance(parts, list):
                text_parts = [{"text": p} if isinstance(p, str) else p for p in parts]
                contents.append({"role": role, "parts": text_parts})

        # Inject context on first message
        user_text = req.message
        if req.include_context and not req.conversation_history:
            try:
                summary_data = get_summary()
                context_json = json.dumps(summary_data, ensure_ascii=False, indent=2)
                user_text = (
                    f"<health_data>\n{context_json}\n</health_data>\n\n"
                    f"Use the above data as context.\n\nUser question: {req.message}"
                )
            except Exception as e:
                log.warning(f"Could not fetch summary for AI context: {e}")

        contents.append({"role": "user", "parts": [{"text": user_text}]})

        reply = _gemini_chat(contents, system_instruction=SYSTEM_PROMPT)

        updated_history = [
            *req.conversation_history,
            {"role": "user", "parts": [req.message]},
            {"role": "model", "parts": [reply]},
        ]

        return {"response": reply, "updated_history": updated_history}

    except _requests.HTTPError as e:
        status = e.response.status_code if e.response else 500
        detail = e.response.text[:300] if e.response else str(e)
        log.error(f"Gemini API error {status}: {detail}")
        if status == 429:
            raise HTTPException(429, "Gemini rate limit reached. Vent et øjeblik og prøv igen.")
        raise HTTPException(502, f"Gemini API fejl: {detail}")
    except Exception as e:
        log.error(f"Chat error: {e}")
        raise HTTPException(500, f"Chat fejlede: {str(e)}")


# ---------------------------------------------------------------------------
# ETL trigger
# ---------------------------------------------------------------------------

def _run_etl_background():
    try:
        from etl import ETLPipeline
        ETLPipeline().run_full()
        log.info("Background ETL completed")
    except Exception as e:
        log.error(f"Background ETL failed: {e}")


@app.post("/etl/run")
async def trigger_etl(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_etl_background)
    return {"status": "triggered", "message": "ETL pipeline is running in the background."}


# ---------------------------------------------------------------------------
# Health Connect ingestion (Android companion app)
# ---------------------------------------------------------------------------
# The Android app reads Samsung Health data via the Health Connect API (the
# only supported way to pull Samsung Health data programmatically — Samsung
# has no public cloud API for personal accounts) and POSTs it here. Each
# domain list uses the same column names as the Samsung CSV bronze tables so
# the existing Silver transforms can merge both sources unchanged.

HEALTH_CONNECT_DEDUPE_KEYS = {
    "steps": ["start_time"],
    "heart_rate": ["start_time"],
    "sleep": ["start_time", "end_time"],
    "blood_oxygen": ["start_time"],
    "calories": ["start_time"],
}


class HealthConnectPayload(BaseModel):
    steps: List[dict] = []
    heart_rate: List[dict] = []
    sleep: List[dict] = []
    blood_oxygen: List[dict] = []
    calories: List[dict] = []


def _check_sync_token(x_sync_token: str) -> None:
    if _HEALTH_CONNECT_SYNC_TOKEN and x_sync_token != _HEALTH_CONNECT_SYNC_TOKEN:
        raise HTTPException(401, "Invalid or missing X-Sync-Token header")


@app.post("/ingest/health_connect")
async def ingest_health_connect(
    payload: HealthConnectPayload,
    background_tasks: BackgroundTasks,
    auto_etl: bool = True,
    x_sync_token: str = Header(default=""),
):
    """Receive a batch of Health Connect records from the Android sync app."""
    _check_sync_token(x_sync_token)

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ingested: Dict[str, int] = {}

    for domain, dedupe_cols in HEALTH_CONNECT_DEDUPE_KEYS.items():
        records = getattr(payload, domain)
        if not records:
            continue
        try:
            new_df = pd.DataFrame(records)
        except Exception as e:
            raise HTTPException(400, f"Invalid records for '{domain}': {e}")
        new_df["_ingestion_timestamp"] = now
        new_df["_source_filename"] = "health_connect_sync"

        out_path = BRONZE_DIR / f"healthconnect_{domain}.parquet"
        if out_path.exists():
            try:
                existing = pd.read_parquet(out_path)
                new_df = pd.concat([existing, new_df], ignore_index=True)
            except Exception as e:
                log.warning(f"Could not read existing {out_path.name}, overwriting: {e}")

        dedupe_subset = [c for c in dedupe_cols if c in new_df.columns]
        if dedupe_subset:
            new_df = new_df.drop_duplicates(subset=dedupe_subset, keep="last")

        _write_parquet_safe(new_df, out_path)
        ingested[domain] = len(records)

    if not ingested:
        raise HTTPException(400, "No records provided")

    if auto_etl:
        background_tasks.add_task(_run_etl_background)

    return {"status": "ok", "ingested": ingested, "etl_triggered": auto_etl}


def _write_parquet_safe(df: pd.DataFrame, path: Path) -> None:
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df.to_parquet(path, index=False, engine="pyarrow")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
