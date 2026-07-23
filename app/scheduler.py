import time
import threading
from app.database import SessionLocal
from app.config import settings
from app import crud, rss, models

_stop_event = threading.Event()
_thread = None


def poll_all_channels():
    """
    Worker function that connects to the database, gets all registered channels,
    and updates their video libraries from YouTube's RSS feeds.
    """
    db = SessionLocal()
    try:
        channels = crud.get_channels(db)
        print(f"[Scheduler] Starting polling for {len(channels)} channels...")
        for channel in channels:
            if _stop_event.is_set():
                break
            try:
                feed_data = rss.fetch_channel_feed(channel.channel_id)
                new_vids = crud.add_videos_if_not_exists(db, channel.channel_id, feed_data["videos"])
                crud.update_channel_polled(db, channel.channel_id)
                if len(new_vids) > 0:
                    print(f"[Scheduler] Polled '{channel.title}': added {len(new_vids)} new videos.")
            except Exception as e:
                print(f"[Scheduler] Error polling channel '{channel.title}' ({channel.channel_id}): {e}")
    finally:
        db.close()


def clean_existing_videos():
    """
    On startup, prune every channel's video list to the 2 latest entries.
    Shorts are now excluded at the feed (UULF playlist) level, so no per-video
    HTTP scanning is needed here.
    """
    db = SessionLocal()
    try:
        channels = db.query(models.Channel).all()
        print(f"[Scheduler] Pruning videos to 2 latest per subscription for {len(channels)} channels...")
        for channel in channels:
            if _stop_event.is_set():
                break
            crud.prune_videos_for_channel(db, channel.channel_id)
        print("[Scheduler] Startup pruning complete.")
    except Exception as e:
        print(f"[Scheduler] Error during startup pruning: {e}")
    finally:
        db.close()


def _worker_loop():
    print("[Scheduler] Background scheduler loop started.")
    # Run once at startup
    poll_all_channels()

    # Start existing database clean-up and pruning in a separate thread so it does not block the polling scheduler loop
    threading.Thread(target=clean_existing_videos, daemon=True).start()

    while not _stop_event.is_set():
        # Sleep in 1-second intervals to allow responsive shutdown
        interval = settings.poll_interval
        for _ in range(interval):
            if _stop_event.is_set():
                break
            time.sleep(1)

        if not _stop_event.is_set():
            poll_all_channels()

    print("[Scheduler] Background scheduler loop stopped.")


def start_scheduler():
    global _thread, _stop_event
    if _thread is not None and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_worker_loop, daemon=True)
    _thread.start()


def stop_scheduler():
    global _thread, _stop_event
    _stop_event.set()
    if _thread is not None:
        _thread.join(timeout=5)
