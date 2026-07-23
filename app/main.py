from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.routes import router
from app.scheduler import start_scheduler, stop_scheduler

# Initialize database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the RSS feed polling scheduler in the background
    start_scheduler()
    yield
    # Stop the scheduler thread on application shutdown
    stop_scheduler()


app = FastAPI(
    title=settings.app_title,
    description="A lightweight self-hosted YouTube subscription tracker via RSS feeds.",
    version="0.1.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include the routes router
app.include_router(router)
