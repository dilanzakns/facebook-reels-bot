import os
import sys
import time
import argparse
from datetime import datetime
import schedule

# Configure utf-8 stdout on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from config import (
    POST_INTERVAL_HOURS, PROCESSED_CLIPS_DIR, RAW_CLIPS_DIR,
    GEMINI_API_KEY, FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN
)
from database import init_db, update_clip_processed, mark_as_uploaded
from clip_fetcher import get_next_viral_clip
from ai_captioner import generate_viral_metadata
from voice_engine import generate_voiceover_and_subtitles
from video_processor import render_vertical_reel
from fb_uploader import upload_video_to_facebook, verify_facebook_token, is_fb_configured

def run_pipeline(dry_run: bool = False) -> bool:
    """
    Executes 1 full automated cycle for High-Reach, Monetization-Ready Reels:
    1. Fetch next viral sports comedy / impossible clip
    2. Generate catchy Hook, Commentary Script, and Caption with AI
    3. Generate AI Commentary Voiceover & Subtitles with Edge-TTS
    4. Render 9:16 vertical Reel with blurred canvas, banner, watermark & mixed audio
    5. Auto upload to Facebook Page
    6. Save record in database
    """
    print("\n" + "="*60)
    print(f"🚀 RUNNING HIGH-REACH MONETIZATION REEL PIPELINE ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*60)

    # 1. Fetch Clip
    clip_info = get_next_viral_clip()
    if not clip_info:
        print("[!] No new clip available right now. Will check on next cycle.")
        return False

    clip_id = clip_info["clip_id"]
    original_title = clip_info["title"]
    raw_video_path = clip_info["file_path"]

    print(f"\n[1/5] Selected Clip: '{original_title}' (ID: {clip_id})")

    # 2. Generate Viral Metadata (Hook, Commentary, Caption, Tags)
    print("\n[2/5] Generating AI Viral Hook & Commentary Script...")
    meta = generate_viral_metadata(original_title)
    hook_text = meta["hook_text"]
    commentary_script = meta.get("commentary_script", "")
    caption = meta["caption"]

    print(f"      📌 Hook Banner: {hook_text}")
    print(f"      🎙️ AI Commentary Script: {commentary_script}")
    print(f"      📝 Caption Preview: {caption[:80]}...")

    # 3. Generate AI Voiceover
    print("\n[3/5] Generating Realistic AI Voiceover Commentary...")
    voice_data = generate_voiceover_and_subtitles(commentary_script, clip_id)
    voiceover_path = voice_data["audio_path"] if voice_data else None
    srt_path = voice_data["srt_path"] if voice_data else None

    # 4. Render 9:16 Vertical Reel
    print("\n[4/5] Rendering 9:16 Monetization-Ready Video Reel...")
    output_filename = f"reel_{clip_id}.mp4"
    processed_video_path = render_vertical_reel(
        raw_video_path=raw_video_path,
        hook_text=hook_text,
        output_filename=output_filename,
        voiceover_path=voiceover_path,
        srt_path=srt_path
    )

    if not processed_video_path:
        print("[-] Video rendering failed. Aborting upload.")
        return False

    update_clip_processed(clip_id, hook_text, processed_video_path)

    # 5. Upload to Facebook Page
    print("\n[5/5] Uploading to Facebook Page...")
    if dry_run:
        print("[*] Dry-run enabled. Skipping actual upload.")
        print(f"[+] Output ready at: {processed_video_path}")
        return True

    fb_id = upload_video_to_facebook(
        video_path=processed_video_path,
        title=hook_text,
        caption=caption
    )

    if fb_id:
        mark_as_uploaded(clip_id, fb_id)
        print("\n🎉 PIPELINE CYCLE COMPLETED SUCCESSFULLY!")
        return True
    else:
        print("\n[-] Upload could not be completed.")
        return False

def start_scheduler():
    """Starts the 24/7 scheduler that runs automatically while you sleep."""
    print("\n" + "="*60)
    print(f"⏰ STARTING 24/7 AUTO-POSTING BOT (MONETIZATION & VIRAL REACH)")
    print(f"⏰ Configured interval: Every {POST_INTERVAL_HOURS} hours")
    print(f"⏰ Target niche: Sport Comedy / Funny + Impossible Moments")
    print("="*60 + "\n")

    if not is_fb_configured():
        print("[!] Facebook credentials not fully set in .env. Bot will run in local simulation mode.")
    else:
        verify_facebook_token()

    # Run initial post immediately
    print("[*] Running immediate first post...")
    run_pipeline()

    # Schedule recurring posts
    schedule.every(POST_INTERVAL_HOURS).hours.do(run_pipeline)

    print(f"\n[+] Scheduler active! Next run in {POST_INTERVAL_HOURS} hours. Press Ctrl+C to stop.\n")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user.")

def main():
    parser = argparse.ArgumentParser(description="Automated Sport Comedy & Impossible Video Bot for Facebook Reels")
    parser.add_argument("--run-once", action="store_true", help="Run 1 automated cycle immediately and exit")
    parser.add_argument("--schedule", action="store_true", help="Start the 24/7 automated scheduler")
    parser.add_argument("--test", action="store_true", help="Run pipeline in test mode (processes video without uploading)")
    parser.add_argument("--verify-fb", action="store_true", help="Test connection to Facebook Page")

    args = parser.parse_args()

    init_db()

    if args.verify_fb:
        verify_facebook_token()
    elif args.test:
        run_pipeline(dry_run=True)
    elif args.run_once:
        run_pipeline(dry_run=False)
    elif args.schedule:
        start_scheduler()
    else:
        print("Sport Comedy / Impossible Moments Facebook Reel Automation Bot")
        print("----------------------------------------------------------------")
        print("Usage:")
        print("  py main.py --run-once   : Download, add AI Voiceover, edit, and upload 1 video right now")
        print("  py main.py --schedule   : Run 24/7 auto posting while you sleep")
        print("  py main.py --test       : Process a video to preview without uploading")
        print("  py main.py --verify-fb  : Check Facebook Page token & permissions\n")
        
        run_pipeline(dry_run=True)

if __name__ == "__main__":
    main()
