import os
import sys
import asyncio
import edge_tts
from pathlib import Path
from typing import Dict, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from config import TEMP_DIR

# Viral narrator voices
VOICE_OPTIONS = [
    "en-US-ChristopherNeural",  # Energetic, engaging storytelling
    "en-US-GuyNeural",          # Classic American hype narrator
    "en-US-EricNeural"          # Sarcastic / comedy narrator
]

async def _generate_voiceover_async(text: str, output_audio_path: str, output_srt_path: str, voice: str = "en-US-ChristopherNeural") -> bool:
    """
    Generates realistic AI voiceover and word-synced subtitles using Edge-TTS.
    """
    try:
        communicate = edge_tts.Communicate(text, voice, rate="+8%")
        submaker = edge_tts.SubMaker()

        with open(output_audio_path, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        # Generate styled SRT subtitle file
        with open(output_srt_path, "w", encoding="utf-8") as srt_file:
            srt_file.write(submaker.get_srt())

        return os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 1024
    except Exception as e:
        print(f"[-] Edge-TTS generation failed: {e}")
        return False

def generate_voiceover_and_subtitles(text: str, clip_id: str) -> Optional[Dict[str, str]]:
    """
    Synchronous wrapper for generating voiceover audio and subtitle files.
    """
    audio_path = str(TEMP_DIR / f"voice_{clip_id}.mp3")
    srt_path = str(TEMP_DIR / f"sub_{clip_id}.srt")

    print(f"[*] Generating AI Commentary Voiceover for '{clip_id}'...")
    success = asyncio.run(_generate_voiceover_async(text, audio_path, srt_path))

    if success:
        print(f"[+] Voiceover generated: {audio_path}")
        return {
            "audio_path": audio_path,
            "srt_path": srt_path
        }
    return None

if __name__ == "__main__":
    sample_text = "Wait for the end... Bro really thought he made the save of the century! Watch what happens next!"
    res = generate_voiceover_and_subtitles(sample_text, "test_clip")
    print("Voice result:", res)
