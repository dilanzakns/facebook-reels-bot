import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import imageio_ffmpeg

# Add bundled FFmpeg to PATH so all tools (yt-dlp, subprocess) find it automatically
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = str(Path(ffmpeg_exe).parent)
if ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{ffmpeg_dir};" + os.environ.get("PATH", "")

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
INPUTS_DIR = BASE_DIR / "inputs"
RAW_CLIPS_DIR = BASE_DIR / os.getenv("RAW_CLIPS_DIR", "inputs/raw_clips")
PROCESSED_CLIPS_DIR = BASE_DIR / os.getenv("PROCESSED_CLIPS_DIR", "outputs/ready_to_post")
TEMP_DIR = BASE_DIR / "outputs" / "temp"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = BASE_DIR / "history.db"

# Ensure all needed directories exist
for folder in [INPUTS_DIR, RAW_CLIPS_DIR, PROCESSED_CLIPS_DIR, TEMP_DIR, ASSETS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# API Keys & Credentials
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "").strip()
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()

# Bot Configurations
POST_INTERVAL_HOURS = int(os.getenv("POST_INTERVAL_HOURS", "4"))
TARGET_SUBREDDITS = [
    s.strip() for s in os.getenv("TARGET_SUBREDDITS", "nevertellmetheodds,sports,Unexpected,HoldMyBeer,instant_regret,sportsfails").split(",") if s.strip()
]
WATERMARK_TEXT = os.getenv("WATERMARK_TEXT", "Follow for Daily Impossible Moments 🔥")

# Video Settings (9:16 Vertical Reel standard)
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
FPS = 30
MAX_VIDEO_DURATION_SEC = 60  # Facebook Reels ideal length: under 60 seconds
MIN_VIDEO_DURATION_SEC = 4
