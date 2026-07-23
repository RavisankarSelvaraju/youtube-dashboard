# Save and run as fix_titles.py
from app.database import SessionLocal
from app import crud, rss, models

db = SessionLocal()
try:
    channels = db.query(models.Channel).all()
    for channel in channels:
        try:
            feed_data = rss.fetch_channel_feed(channel.channel_id)
            if feed_data["title"] and feed_data["title"] != "Videos":
                channel.title = feed_data["title"]
                print(f"Updated {channel.channel_id} -> {feed_data['title']}")
        except Exception as e:
            print(f"Error updating {channel.channel_id}: {e}")
    db.commit()
finally:
    db.close()