"""
File watcher — re-runs ETL pipeline when new files are added to DATA/
Also polls Strava for new runs on a timer, so running data stays fresh
without any manual export at all.
"""

import logging
import subprocess
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "DATA"
ETL_SCRIPT = BASE_DIR / "etl.py"
STRAVA_SYNC_SCRIPT = BASE_DIR / "strava_sync.py"
COOLDOWN_SECONDS = 30
WATCHED_EXTENSIONS = {".csv", ".json", ".txt", ".xlsx"}
STRAVA_SYNC_INTERVAL_SECONDS = 30 * 60


def run_subprocess(script: Path, label: str, timeout: int = 300) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            log.info(f"{label} completed successfully")
            if result.stdout:
                log.info(result.stdout[-500:])  # last 500 chars
            return True
        else:
            log.error(f"{label} failed (exit {result.returncode}):\n{result.stderr[-1000:]}")
            return False
    except subprocess.TimeoutExpired:
        log.error(f"{label} timed out after {timeout}s")
        return False
    except Exception as e:
        log.error(f"{label} error: {e}")
        return False


def run_etl() -> bool:
    return run_subprocess(ETL_SCRIPT, "ETL")


class ETLTriggerHandler(FileSystemEventHandler):
    def __init__(self):
        self._last_triggered: float = 0.0

    def on_created(self, event: FileCreatedEvent):
        if not event.is_directory:
            self._maybe_trigger(event.src_path)

    def on_modified(self, event: FileModifiedEvent):
        if not event.is_directory:
            self._maybe_trigger(event.src_path)

    def _maybe_trigger(self, path: str) -> None:
        if Path(path).suffix.lower() not in WATCHED_EXTENSIONS:
            return
        now = time.time()
        if now - self._last_triggered < COOLDOWN_SECONDS:
            log.info(f"Debouncing ETL (cooldown active): {path}")
            return
        self._last_triggered = now
        log.info(f"File change detected: {path} — triggering ETL...")
        run_etl()


def _strava_sync_loop(stop_event: threading.Event) -> None:
    """Polls Strava for new runs every STRAVA_SYNC_INTERVAL_SECONDS and re-runs ETL
    when new activities were found — fully automatic, no manual export needed."""
    if not STRAVA_SYNC_SCRIPT.exists():
        return
    while not stop_event.is_set():
        log.info("Running scheduled Strava sync...")
        if run_subprocess(STRAVA_SYNC_SCRIPT, "Strava sync", timeout=60):
            run_etl()
        stop_event.wait(STRAVA_SYNC_INTERVAL_SECONDS)


def main() -> None:
    if not DATA_DIR.exists():
        log.error(f"DATA directory not found: {DATA_DIR}")
        sys.exit(1)

    handler = ETLTriggerHandler()
    observer = Observer()
    observer.schedule(handler, str(DATA_DIR), recursive=True)
    observer.start()
    log.info(f"Watching {DATA_DIR} for changes (extensions: {WATCHED_EXTENSIONS})...")

    stop_event = threading.Event()
    strava_thread = threading.Thread(
        target=_strava_sync_loop, args=(stop_event,), daemon=True
    )
    strava_thread.start()
    log.info(f"Polling Strava for new runs every {STRAVA_SYNC_INTERVAL_SECONDS // 60} min...")
    log.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping scheduler...")
    finally:
        stop_event.set()
        observer.stop()
        observer.join()
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
