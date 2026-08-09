# youtube-dashboard

A self-hosted YouTube subscription tracker. Subscribe to channels by URL/handle/ID, and it polls their RSS feeds in the background so you get a simple "new videos" dashboard without needing a YouTube API key.

## What this is

`app/main.py` is a FastAPI app. On startup it starts a background scheduler thread (`app/scheduler.py`) that polls every subscribed channel's RSS feed every `POLL_INTERVAL` seconds (default 600s / 10 min), fetching new videos and storing them in a SQLite database (`youtube_tracker.db`).

- `app/rss.py` — resolves a channel URL/handle/ID to a raw channel ID, and parses YouTube's Atom RSS feeds. Prefers the `UULF` (long-form only, Shorts-excluded) feed and falls back to the full uploads feed if that's empty.
- `app/models.py` / `app/database.py` — SQLAlchemy models (`Channel`, `Video`) and session setup.
- `app/crud.py` — database read/write helpers used by routes and the scheduler.
- `app/routes.py` — the dashboard page (`/`) plus a small JSON API for subscribing/unsubscribing, forcing a poll, and marking videos watched/bookmarked.
- `app/templates/index.html` — the dashboard UI (channel sidebar, filters, search).
- `fix-titles.py` — one-off script to re-fetch and fix channel titles that were saved incorrectly (e.g. as "Videos").

The dashboard supports filtering by channel, by status (all / unwatched / bookmarked), and a fuzzy text search over video title/description.

## Requirements

- Python 3
- `tmux` (optional, used by `run.bash` for a detached background run)

## Setup

```bash
bash setup.bash
```

Creates a venv named `dashboard` and installs `requirements.txt` into it. Skips creation if a venv already exists in the directory.

## Configuration

Optional `.env` file (or environment variables) in the project root:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./youtube_tracker.db` | SQLAlchemy database URL |
| `POLL_INTERVAL` | `600` | Seconds between RSS polls |
| `BASE_PATH` | `""` | External mount prefix (e.g. `/youtube-dashboard`) — see [Tailnet routing](#tailnet-routing) |

## Run

```bash
bash run.bash
```

If `tmux` is available, this starts the app in a detached session named `youtube_tracker`; otherwise it runs in the foreground. Either way it calls `python3 run.py`, which starts uvicorn on `http://0.0.0.0:8000`.

Attach to the tmux session: `tmux attach -t youtube_tracker` (detach with `Ctrl-b` then `d`).

To stop it, kill the tmux session (`tmux kill-session -t youtube_tracker`) or the `uvicorn`/`python3 run.py` process if running in the foreground.

## Use

Open `http://localhost:8000`. Subscribe to a channel by pasting its URL, `@handle`, or raw `UC...` ID into the subscribe form. New videos show up after the next poll (or immediately via the "poll now" API endpoints below).

Also reachable tailnet-wide at `https://groot.tail088f09.ts.net/youtube-dashboard`, mounted alongside Nextcloud and camera-server on the same hostname via `tailscale serve` (see [Tailnet routing](#tailnet-routing)).

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/channels` | Subscribe to a channel (accepts URL/handle/ID) |
| `DELETE` | `/api/channels/{channel_id}` | Unsubscribe |
| `PATCH` | `/api/channels/{channel_id}` | Rename a channel's stored title |
| `POST` | `/api/channels/{channel_id}/poll` | Force-poll a single channel now |
| `POST` | `/api/channels/poll` | Force-poll all channels now |
| `PUT` | `/api/videos/{video_id}` | Update a video's watched/bookmarked status |

## Files

| File | Purpose |
|---|---|
| `run.py` | Entrypoint, starts uvicorn |
| `run.bash` | Activates the venv and starts the app (tmux if available) |
| `setup.bash` | Creates the `dashboard` venv and installs dependencies |
| `quick-push.sh` | Convenience `git add -A && git commit && git push` |
| `fix-titles.py` | One-off maintenance script to re-fetch channel titles |
| `dashboard/` | Virtual environment (not portable — recreate with `setup.bash`) |
| `youtube_tracker.db` | SQLite database (created on first run) |

## Notes

- No YouTube API key required — everything is read from public RSS feeds, so subscription counts and features are limited to what the feed exposes (recent uploads only, not full channel history).
- The scheduler also prunes stored videos down to the 2 most recent per channel on startup and removes any misclassified Shorts, since the `UULF` feed's Shorts filtering isn't perfect.

## Tailnet routing

`run.bash` sets `BASE_PATH=/youtube-dashboard` when launching the app. `app/routes.py` passes it into every template render as `base_path`, and `app/templates/index.html` prefixes all its hardcoded links, form actions, the stylesheet `<link>`, and its `fetch()`/`location.href` calls with it (via a `BASE_PATH` JS constant). This is needed because the browser resolves absolute paths like `/static/...` or `/api/...` against the domain root, not wherever the page itself was mounted — without the prefix those requests would miss this app entirely and hit whatever else is mounted at `/`. Running the app directly (`python3 run.py`, no `BASE_PATH` set) is unaffected and serves normally at the root.

The tailnet-wide mount is configured once on the host via:

```bash
tailscale serve --bg --set-path=/youtube-dashboard 8000
```

`tailscale serve` strips the `/youtube-dashboard` prefix before forwarding to this app, so the app's own routes and API don't need to know about the prefix — only the browser-facing URLs generated in the template do, which is what `BASE_PATH` handles.
