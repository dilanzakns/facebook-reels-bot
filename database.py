import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                original_title TEXT,
                ai_hook_title TEXT,
                raw_file_path TEXT,
                processed_file_path TEXT,
                fb_video_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_at TIMESTAMP
            )
        """)
        conn.commit()

def is_clip_processed(clip_id: str) -> bool:
    """Checks if a clip has already been processed or uploaded."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM processed_clips WHERE clip_id = ?", (clip_id,))
        return cursor.fetchone() is not None

def record_clip(
    clip_id: str,
    source: str,
    original_title: str,
    raw_file_path: str = "",
    status: str = "downloaded"
) -> int:
    """Records a new downloaded clip into the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO processed_clips (clip_id, source, original_title, raw_file_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (clip_id, source, original_title, raw_file_path, status, datetime.now()))
        conn.commit()
        return cursor.lastrowid

def update_clip_processed(clip_id: str, ai_hook_title: str, processed_file_path: str):
    """Updates clip status once video editing is completed."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE processed_clips
            SET ai_hook_title = ?, processed_file_path = ?, status = 'processed'
            WHERE clip_id = ?
        """, (ai_hook_title, processed_file_path, clip_id))
        conn.commit()

def mark_as_uploaded(clip_id: str, fb_video_id: str):
    """Marks a clip as uploaded to Facebook with its FB Video ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE processed_clips
            SET fb_video_id = ?, status = 'uploaded', uploaded_at = ?
            WHERE clip_id = ?
        """, (fb_video_id, datetime.now(), clip_id))
        conn.commit()

# Auto-initialize database on import
init_db()
