import os
import sys
import glob
import random
import hashlib
import yt_dlp
from pathlib import Path
from typing import Optional, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from config import RAW_CLIPS_DIR, MIN_VIDEO_DURATION_SEC, MAX_VIDEO_DURATION_SEC
from database import is_clip_processed, record_clip

VIRAL_SEARCH_QUERIES = [
    "impossible sports moments shorts",
    "funny sports comedy moments shorts",
    "unbelievable sports tricks 9999 iq shorts",
    "funniest sports fails bloopers shorts",
    "1 in a million sports moments shorts",
    "accidental genius sports plays shorts",
    "instant regret sports comedy shorts",
    "crazy sports trickshots impossible shorts"
]

def get_clip_from_local_folder() -> Optional[Dict[str, Any]]:
    extensions = ["*.mp4", "*.mov", "*.mkv", "*.webm"]
    all_files = []
    for ext in extensions:
        all_files.extend(RAW_CLIPS_DIR.glob(ext))
    
    for video_file in all_files:
        clip_id = f"local_{hashlib.md5(video_file.name.encode()).hexdigest()[:10]}"
        if not is_clip_processed(clip_id):
            clean_title = video_file.stem.replace("_", " ").replace("-", " ")
            record_clip(
                clip_id=clip_id,
                source="local_folder",
                original_title=clean_title,
                raw_file_path=str(video_file),
                status="downloaded"
            )
            return {
                "clip_id": clip_id,
                "title": clean_title,
                "file_path": str(video_file),
                "source": "local"
            }
    return None

def fetch_clip_from_viral_search() -> Optional[Dict[str, Any]]:
    queries = list(VIRAL_SEARCH_QUERIES)
    random.shuffle(queries)

    extractor_args = {
        'youtube': {
            'player_client': ['android']
        }
    }

    for query in queries:
        print(f"[*] Searching viral clips for query: '{query}'...")
        search_target = f"ytsearch15:{query}"

        ydl_opts_extract = {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'extractor_args': extractor_args
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts_extract) as ydl:
                result = ydl.extract_info(search_target, download=False)
                entries = result.get('entries', []) if result else []

            for entry in entries:
                if not entry:
                    continue
                video_id = entry.get('id')
                if not video_id:
                    continue
                
                clip_id = f"yt_{video_id}"
                if is_clip_processed(clip_id):
                    continue

                title = entry.get('title', 'Amazing Sports Moment')
                duration = entry.get('duration', 30)

                if duration and (duration < MIN_VIDEO_DURATION_SEC or duration > MAX_VIDEO_DURATION_SEC):
                    continue

                url = f"https://www.youtube.com/watch?v={video_id}"
                target_filename = f"{clip_id}.mp4"
                target_path = str(RAW_CLIPS_DIR / target_filename)

                print(f"[+] Downloading viral candidate: '{title}'...")

                ydl_opts_download = {
                    'format': 'best',
                    'outtmpl': target_path,
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': extractor_args
                }

                with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_down:
                    ydl_down.download([url])

                if os.path.exists(target_path) and os.path.getsize(target_path) > 1024:
                    record_clip(
                        clip_id=clip_id,
                        source="viral_search",
                        original_title=title,
                        raw_file_path=target_path,
                        status="downloaded"
                    )
                    return {
                        "clip_id": clip_id,
                        "title": title,
                        "file_path": target_path,
                        "source": "viral_search"
                    }
        except Exception as e:
            print(f"[-] Search error for '{query}': {e}")
            continue

    return None

def get_next_viral_clip() -> Optional[Dict[str, Any]]:
    local_clip = get_clip_from_local_folder()
    if local_clip:
        print(f"[+] Using clip from local folder: {local_clip['title']}")
        return local_clip

    viral_clip = fetch_clip_from_viral_search()
    if viral_clip:
        return viral_clip

    print("[-] No new clips found.")
    return None

if __name__ == "__main__":
    clip = get_next_viral_clip()
    print("Fetched clip:", clip)
