"""
Pulls new running activities from the Strava API and appends them to the
Bronze layer, so etl.py can pick them up on the next run.

Requires STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET and STRAVA_REFRESH_TOKEN in
.env (see strava_auth.py for the one-time setup that produces the refresh
token). Safe to run repeatedly — it only fetches activities newer than the
last successful sync (tracked in bronze/.strava_sync_state.json) and skips
Strava API calls entirely when there is nothing new to check yet.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
BRONZE_DIR = BASE_DIR / "bronze"
BRONZE_FILE = BRONZE_DIR / "strava_activities.parquet"
STATE_FILE = BRONZE_DIR / ".strava_sync_state.json"

CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("STRAVA_REFRESH_TOKEN")

# Re-fetch a small overlap window so edited/merged activities near the
# boundary aren't missed.
OVERLAP = timedelta(days=2)


def _get_access_token() -> str:
    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def _save_state(state: dict) -> None:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


def _fetch_activities(access_token: str, after_epoch: int) -> list:
    activities = []
    page = 1
    headers = {"Authorization": f"Bearer {access_token}"}
    while True:
        resp = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers=headers,
            params={"after": after_epoch, "per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        activities.extend(batch)
        page += 1
    return activities


def sync() -> int:
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        log.warning("Strava credentials missing in .env — skipping sync. See strava_auth.py.")
        return 0

    state = _load_state()
    last_sync = state.get("last_synced_at")
    if last_sync:
        after_dt = datetime.fromisoformat(last_sync) - OVERLAP
    else:
        after_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
    after_epoch = int(after_dt.timestamp())

    access_token = _get_access_token()
    activities = _fetch_activities(access_token, after_epoch)
    runs = [a for a in activities if a.get("type") == "Run" or a.get("sport_type") == "Run"]

    if not runs:
        log.info("Strava sync: no new runs.")
        _save_state({"last_synced_at": datetime.now(timezone.utc).isoformat()})
        return 0

    new_df = pd.json_normalize(runs)
    new_df["_ingestion_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_df["_source_filename"] = "strava_api"

    if BRONZE_FILE.exists():
        existing = pd.read_parquet(BRONZE_FILE)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["id"], keep="last")
    else:
        combined = new_df

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(BRONZE_FILE, index=False, engine="pyarrow")
    _save_state({"last_synced_at": datetime.now(timezone.utc).isoformat()})

    log.info(f"Strava sync: {len(runs)} new run(s) fetched, {len(combined)} total in bronze.")
    return len(runs)


if __name__ == "__main__":
    sync()
