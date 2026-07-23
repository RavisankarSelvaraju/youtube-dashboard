from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List

from app import crud, schemas, rss, database

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# HTML Dashboard View
@router.get("/", response_class=HTMLResponse)
def dashboard_view(
    request: Request,
    channel_id: Optional[str] = None,
    filter_type: str = "unwatched",  # "all", "unwatched", "bookmarked"
    q: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    # Fetch channels for sidebar
    channels = crud.get_channels(db)

    is_watched = None
    is_bookmarked = None

    if filter_type == "unwatched":
        is_watched = False
    elif filter_type == "bookmarked":
        is_bookmarked = True

    # Get videos matching the status filters
    videos = crud.get_videos(
        db,
        channel_id=channel_id,
        is_watched=is_watched,
        is_bookmarked=is_bookmarked,
        limit=100
    )

    # Fuzzy title filter if search string is provided
    if q:
        q_lower = q.lower()
        videos = [
            v for v in videos
            if q_lower in v.title.lower() or (v.description and q_lower in v.description.lower())
        ]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "channels": channels,
            "videos": videos,
            "active_channel_id": channel_id,
            "active_filter": filter_type,
            "search_query": q or ""
        }
    )


# API: Subscription Management
@router.post("/api/channels", response_model=schemas.ChannelResponse)
def subscribe_channel(
    payload: schemas.ChannelCreate,
    db: Session = Depends(database.get_db)
):
    # Resolve handle/URL/raw ID to raw 24-character channel ID
    channel_id = rss.extract_channel_id(payload.channel_id)
    if not channel_id:
        raise HTTPException(
            status_code=400,
            detail="Could not extract channel ID. Please provide a valid channel URL or UC... ID."
        )

    # Check if already subscribed
    existing = crud.get_channel_by_yt_id(db, channel_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Channel is already subscribed."
        )

    # Fetch initial feed to get metadata (like the official title)
    try:
        feed_data = rss.fetch_channel_feed(channel_id)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch YouTube RSS feed: {e}"
        )

    # Save to database
    new_channel = schemas.ChannelCreate(
        channel_id=channel_id,
        title=feed_data["title"] or payload.title or "Unknown Channel",
        custom_url=feed_data["custom_url"] or payload.custom_url,
        thumbnail_url=payload.thumbnail_url,
        description=payload.description
    )
    db_channel = crud.create_channel(db, new_channel)

    # Backfill with the initial videos from feed
    crud.add_videos_if_not_exists(db, channel_id, feed_data["videos"])

    return db_channel


@router.delete("/api/channels/{channel_id}")
def unsubscribe_channel(
    channel_id: str,
    db: Session = Depends(database.get_db)
):
    success = crud.delete_channel(db, channel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Channel not found.")
    return {"message": "Successfully unsubscribed from channel."}


@router.post("/api/channels/{channel_id}/poll")
def force_poll_channel(
    channel_id: str,
    db: Session = Depends(database.get_db)
):
    channel = crud.get_channel_by_yt_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")

    try:
        feed_data = rss.fetch_channel_feed(channel_id)
        new_vids = crud.add_videos_if_not_exists(db, channel_id, feed_data["videos"])
        crud.update_channel_polled(db, channel_id)
        return {"message": "Polled successfully.", "new_videos_count": len(new_vids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Polling failed: {e}")


@router.post("/api/channels/poll")
def force_poll_all_channels(
    db: Session = Depends(database.get_db)
):
    channels = crud.get_channels(db)
    polled_count = 0
    new_vids_count = 0

    for channel in channels:
        try:
            feed_data = rss.fetch_channel_feed(channel.channel_id)
            new_vids = crud.add_videos_if_not_exists(db, channel.channel_id, feed_data["videos"])
            crud.update_channel_polled(db, channel.channel_id)
            polled_count += 1
            new_vids_count += len(new_vids)
        except Exception:
            continue

    return {
        "message": f"Polled {polled_count} channels.",
        "new_videos_count": new_vids_count
    }


# API: Video Interaction
@router.put("/api/videos/{video_id}", response_model=schemas.VideoResponse)
def update_video(
    video_id: str,
    payload: schemas.VideoUpdate,
    db: Session = Depends(database.get_db)
):
    video = crud.update_video_status(
        db,
        video_id=video_id,
        is_watched=payload.is_watched,
        is_bookmarked=payload.is_bookmarked
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    return video

# app/routes.py
from pydantic import BaseModel

class ChannelUpdate(BaseModel):
    title: str

@router.patch("/api/channels/{channel_id}")
def rename_channel(
    channel_id: str,
    payload: ChannelUpdate,
    db: Session = Depends(database.get_db)
):
    channel = crud.update_channel_title(db, channel_id=channel_id, new_title=payload.title)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found.")
    return channel