from __future__ import annotations
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from .cli import ingest_two_years

def _job():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Daily two-year backfill starting...")
    ingest_two_years()
    print(f"[{datetime.now(timezone.utc).isoformat()}] Done.")

def main(run_days: int = 7):
    sched = BlockingScheduler(timezone="UTC")
    sched.add_job(_job, "interval", days=1, next_run_time=datetime.now(timezone.utc))
    end_time = datetime.now(timezone.utc) + timedelta(days=run_days, seconds=5)
    try:
        while datetime.now(timezone.utc) < end_time:
            sched._main_loop()
    finally:
        try: sched.shutdown(wait=False)
        except Exception: pass

if __name__ == "__main__":
    main(run_days=7)
