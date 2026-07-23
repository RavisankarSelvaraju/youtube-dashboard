from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional, Dict, Any
from app import models, schemas


# Channel operations
def get_channel(db: Session, channel_db_id: int) -> Optional[models.Channel]:
    return db.query(models.Channel).filter(models.Channel.id == channel_db_id).first()


def get_channel_by_yt_id(db: Session, channel_id: str) -> Optional[models.Channel]:
    return db.query(models.Channel).filter(models.Channel.channel_id == channel_id).first()


def get_channels(db: Session, skip: int = 0, limit: int = 100) -> List[models.Channel]:
    return db.query(models.Channel).offset(skip).limit(limit).all()


def create_channel(db: Session, channel: schemas.ChannelCreate) -> models.Channel:
    db_channel = models.Channel(
        channel_id=channel.channel_id,
        title=channel.title,
        custom_url=channel.custom_url,
        thumbnail_url=channel.thumbnail_url,
        description=channel.description,
        added_at=datetime.utcnow()
    )
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel


def delete_channel(db: Session, channel_id: str) -> bool:
    db_channel = db.query(models.Channel).filter(models.Channel.channel_id == channel_id).first()
    if db_channel:
        db.delete(db_channel)
        db.commit()
        return True
    return False


def update_channel_polled(db: Session, channel_id: str) -> Optional[models.Channel]:
    db_channel = db.query(models.Channel).filter(models.Channel.channel_id == channel_id).first()
    if db_channel:
        db_channel.last_polled_at = datetime.utcnow()
        db.commit()
        db.refresh(db_channel)
    return db_channel


# Video operations
def get_video(db: Session, video_id: str) -> Optional[models.Video]:
    return db.query(models.Video).filter(models.Video.video_id == video_id).first()


def get_videos(
    db: Session,
    channel_id: Optional[str] = None,
    is_watched: Optional[bool] = None,
    is_bookmarked: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50
) -> List[models.Video]:
    query = db.query(models.Video).options(joinedload(models.Video.channel))
    
    if channel_id is not None:
        query = query.filter(models.Video.channel_id == channel_id)
    if is_watched is not None:
        query = query.filter(models.Video.is_watched == is_watched)
    if is_bookmarked is not None:
        query = query.filter(models.Video.is_bookmarked == is_bookmarked)
        
    return query.order_by(desc(models.Video.published_at)).offset(skip).limit(limit).all()


def add_videos_if_not_exists(db: Session, channel_id: str, videos_data: List[Dict[str, Any]]) -> List[models.Video]:
    """
    Add up to 2 videos from the RSS feed to the database for this channel.
    The feed data comes from the UULF (Videos-only) playlist so Shorts are
    already excluded at the source.
    """
    MAX_PER_CHANNEL = 2

    new_videos = []
    stored_count = 0  # confirmed non-Short videos for this channel

    for video in videos_data:
        if stored_count >= MAX_PER_CHANNEL:
            break

        exists = db.query(models.Video).filter(models.Video.video_id == video["video_id"]).first()
        if exists:
            stored_count += 1
            continue

        db_video = models.Video(
            video_id=video["video_id"],
            channel_id=channel_id,
            title=video["title"],
            description=video["description"],
            published_at=video["published_at"],
            thumbnail_url=video["thumbnail_url"],
            video_url=video["video_url"],
            is_watched=False,
            is_bookmarked=False,
            added_at=datetime.utcnow()
        )
        db.add(db_video)
        new_videos.append(db_video)
        stored_count += 1

    if new_videos:
        db.commit()
        for v in new_videos:
            db.refresh(v)

    prune_videos_for_channel(db, channel_id)
    return new_videos


def prune_videos_for_channel(db: Session, channel_id: str):
    """
    Keep only the 2 latest videos (by published_at desc) and any bookmarked videos
    for a given channel, deleting the rest.
    """
    # Get all videos for the channel, sorted by published_at DESC
    videos = (
        db.query(models.Video)
        .filter(models.Video.channel_id == channel_id)
        .order_by(desc(models.Video.published_at))
        .all()
    )
    
    # We want to keep:
    # 1. The 2 latest videos (indexes 0 and 1 in the sorted list)
    # 2. Any videos where is_bookmarked is True
    to_keep = set()
    for v in videos[:2]:
        to_keep.add(v.video_id)
    for v in videos:
        if v.is_bookmarked:
            to_keep.add(v.video_id)
            
    # Delete any video not in the keep set
    deleted_count = 0
    for v in videos:
        if v.video_id not in to_keep:
            db.delete(v)
            deleted_count += 1
            
    if deleted_count > 0:
        db.commit()
        print(f"[Pruner] Deleted {deleted_count} old videos for channel {channel_id}.")


def update_video_status(
    db: Session,
    video_id: str,
    is_watched: Optional[bool] = None,
    is_bookmarked: Optional[bool] = None
) -> Optional[models.Video]:
    db_video = db.query(models.Video).filter(models.Video.video_id == video_id).first()
    if db_video:
        if is_watched is not None:
            db_video.is_watched = is_watched
        if is_bookmarked is not None:
            db_video.is_bookmarked = is_bookmarked
        db.commit()
        db.refresh(db_video)
    return db_video
