from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

try:
    from pydantic import ConfigDict
    HAS_V2 = True
except ImportError:
    HAS_V2 = False


class ORMCompatibleModel(BaseModel):
    if HAS_V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


# Video schemas
class VideoBase(ORMCompatibleModel):
    video_id: str
    channel_id: str
    title: str
    description: Optional[str] = None
    published_at: datetime
    thumbnail_url: Optional[str] = None
    video_url: str
    is_watched: bool = False
    is_bookmarked: bool = False


class VideoCreate(VideoBase):
    pass


class VideoUpdate(BaseModel):
    is_watched: Optional[bool] = None
    is_bookmarked: Optional[bool] = None


class VideoResponse(VideoBase):
    id: int
    added_at: datetime


# Channel schemas
class ChannelBase(ORMCompatibleModel):
    channel_id: str
    title: str
    custom_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelResponse(ChannelBase):
    id: int
    added_at: datetime
    last_polled_at: Optional[datetime] = None


# Detailed channel response including videos
class ChannelDetailResponse(ChannelResponse):
    videos: List[VideoResponse] = []
