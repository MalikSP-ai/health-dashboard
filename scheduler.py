"""
File watcher — re-runs ETL pipeline when new files are added to DATA/
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "DATA"
ETL_SCRIPT = Path(__file__).parent / "etl.py"
COOLDOWN_SECONDS = 30
WATCHED_EXTENSIONS = {".csv", ".json", ".txt", ".xlsx"}


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
        self._run_etl()

    def _run_etl(self) -> None:
        try:
            result = subprocess.run(
                [sys.executable, str(ETL_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                log.info("ETL completed successfully")
                if result.stdout:
                    log.info(result.stdout[-500:])  # last 500 chars
            else:
                log.error(f"ETL failed (exit {result.returncode}):\n{result.stderr[-1000:]}")
        except subprocess.TimeoutExpired:
            log.error("ETL timed out after 5 minutes")
        except Exception as e:
            log.error(f"ETL trigger error: {e}")


def main() -> None:
    if not DATA_DIR.exists():
        log.error(f"DATA directory not found: {DATA_DIR}")
        sys.exit(1)

    handler = ETLTriggerHandler()
    observer = Observer()
    observer.schedule(handler, str(DATA_DIR), recursive=True)
    observer.start()
    log.info(f"Watching {DATA_DIR} for changes (extensions: {WATCHED_EXTENSIONS})...")
    log.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping scheduler...")
    finally:
        observer.stop()
        observer.join()
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
