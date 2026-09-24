import os
import sys
import json
import random
import requests
from typing import Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from config import GEMINI_API_KEY

FALLBACK_HOOKS = [
    "BRO THOUGHT HE WAS HIM 💀⚽",
    "HOW IS THIS EVEN POSSIBLE?! 🤯🔥",
    "9999 IQ PLAY OR PURE LUCK? 😱",
    "PHYSICS LEFT THE CHAT 💀⚡",
    "HE RETHOUGHT HIS ENTIRE LIFE 😭",
    "BRO WAS NOT EXPECTING THAT 💀",
    "1 IN A BILLION CHANCE MOMENT 🤯",
    "WHEN THE INTROVERT TRIES SPORTS 💀",
    "HE ALMOST PULLED IT OFF 😭🔥",
    "INSTANT KARMA AT ITS FINEST 💀"
]

FALLBACK_COMMENTARIES = [
    "Wait for the end... Bro really thought he made the play of the century, but watch what actually happens! 💀",
    "There is absolutely no way this happened in real life! Look closely at this impossible moment! 🤯",
    "Bro was celebrating way too early... and instant regret hit him in three, two, one! 😭",
    "Physics definitely stopped working for five seconds right here. How did he actually pull this off?! 😱",
    "He had one job, and ended up creating the funniest moment in sports history! Watch till the end! 💀"
]

FALLBACK_CAPTIONS = [
    "Wait till the very end... 💀 Rate this play from 1 to 10 in the comments! 👇",
    "There is no way this actually happened in real life! 🤯 Follow for more impossible moments! 🔥",
    "Bro really tried his best and it ended like this 😭 What would you do in this situation?",
    "Physics definitely stopped working for a second here 💀 Drop a like if your jaw dropped!",
    "One in a million moment caught on camera! 😱 Tag a friend who needs to see this! 👇"
]

HASHTAGS = "#sportcomedy #impossible #sports #viralreels #funnyvideos #epicfail #sportsbloopers #fbreels #unbelievable #trending"

def generate_viral_metadata(original_title: str) -> Dict[str, str]:
    """
    Generates a viral hook title, hilarious voiceover commentary script,
    Facebook caption, and hashtags using Google Gemini AI.
    """
    if not GEMINI_API_KEY:
        print("[!] GEMINI_API_KEY not set in .env. Using smart viral template engine.")
        hook = random.choice(FALLBACK_HOOKS)
        commentary = random.choice(FALLBACK_COMMENTARIES)
        caption = f"{random.choice(FALLBACK_CAPTIONS)}\n\nOriginal: {original_title}\n\n{HASHTAGS}"
        return {
            "hook_text": hook,
            "commentary_script": commentary,
            "caption": caption,
            "hashtags": HASHTAGS
        }

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        prompt = f"""
You are a viral social media video creator & hype sports commentator for Facebook Reels.
Given this video's original title / context: "{original_title}"

Generate:
1. "hook_text": A short, catchy, uppercase text overlay banner (5-8 words max) with 1-2 funny/shocked emojis (e.g. "BRO THOUGHT HE SCORED 💀⚽", "HOW DID HE DO THIS?! 🤯", "9999 IQ OR 100% LUCK? 😱").
2. "commentary_script": An energetic, funny, hype commentary narration (20-35 words max) for an AI voiceover to speak over the clip. Hook the viewer immediately ("Wait for it...", "Bro thought he was him...", "You won't believe what happens next...").
3. "caption": An engaging Facebook post caption with a call to action asking viewers to comment, vote 1-10, or share.
4. "hashtags": 6-8 trending relevant hashtags like #sportcomedy #impossible #viralreels #fbreels #sportsfails.

Return strictly valid JSON with keys: "hook_text", "commentary_script", "caption", "hashtags".
"""
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_data = response.json()
            candidates = res_data.get("candidates", [])
            if candidates:
                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                result = json.loads(raw_text)
                hook = result.get("hook_text", random.choice(FALLBACK_HOOKS)).strip().upper()
                commentary = result.get("commentary_script", random.choice(FALLBACK_COMMENTARIES)).strip()
                full_caption = f"{result.get('caption', '')}\n\n{result.get('hashtags', HASHTAGS)}"
                return {
                    "hook_text": hook,
                    "commentary_script": commentary,
                    "caption": full_caption,
                    "hashtags": result.get("hashtags", HASHTAGS)
                }

        print(f"[-] Gemini API returned status {response.status_code}. Using fallback.")
    except Exception as e:
        print(f"[-] Gemini AI generation exception ({e}). Falling back to template.")

    hook = random.choice(FALLBACK_HOOKS)
    commentary = random.choice(FALLBACK_COMMENTARIES)
    caption = f"{random.choice(FALLBACK_CAPTIONS)}\n\nOriginal: {original_title}\n\n{HASHTAGS}"
    return {
        "hook_text": hook,
        "commentary_script": commentary,
        "caption": caption,
        "hashtags": HASHTAGS
    }

if __name__ == "__main__":
    test_title = "Goalkeeper accidentally scores in his own goal after celebrating too early"
    meta = generate_viral_metadata(test_title)
    print("Generated Metadata:")
    print(json.dumps(meta, indent=2))
