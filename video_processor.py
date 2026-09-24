import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from config import (
    TARGET_WIDTH, TARGET_HEIGHT, FPS,
    PROCESSED_CLIPS_DIR, TEMP_DIR, WATERMARK_TEXT
)

def get_ffmpeg_binary() -> str:
    """Returns the path to the ffmpeg executable bundled with imageio-ffmpeg."""
    return imageio_ffmpeg.get_ffmpeg_exe()

def create_top_banner_image(hook_text: str, output_image_path: str, width: int = 1080, height: int = 260) -> str:
    """
    Creates a high-contrast viral hook banner image with text wrapping and a modern rounded box.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    box_margin_x = 40
    box_margin_y = 30
    box_rect = [box_margin_x, box_margin_y, width - box_margin_x, height - box_margin_y]
    
    # Dark rounded background box with gold outline
    draw.rounded_rectangle(box_rect, radius=25, fill=(15, 15, 20, 235), outline=(255, 215, 0, 255), width=4)

    font_size = 46
    font = None
    for candidate in [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/tahoma.ttf"
    ]:
        if os.path.exists(candidate):
            try:
                font = ImageFont.truetype(candidate, font_size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    words = hook_text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_w = bbox[2] - bbox[0]
        if text_w <= (width - 140):
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    total_text_height = len(lines) * (font_size + 10)
    start_y = (height - total_text_height) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_x = (width - text_w) // 2
        
        # Black drop shadow
        draw.text((text_x + 3, start_y + 3), line, font=font, fill=(0, 0, 0, 255))
        # Bright Yellow text
        draw.text((text_x, start_y), line, font=font, fill=(255, 235, 59, 255))
        start_y += font_size + 12

    img.save(output_image_path, "PNG")
    return output_image_path

def create_bottom_watermark_image(text: str, output_image_path: str, width: int = 1080, height: int = 100) -> str:
    """Creates a subtle branding watermark for the bottom of the Reel."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = 32
    font = None
    for candidate in ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeui.ttf"]:
        if os.path.exists(candidate):
            try:
                font = ImageFont.truetype(candidate, font_size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pill_w = text_w + 60
    pill_h = text_h + 30
    pill_x = (width - pill_w) // 2
    pill_y = (height - pill_h) // 2
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=20, fill=(0, 0, 0, 190))
    draw.text(((width - text_w) // 2, (height - text_h) // 2 - 2), text, font=font, fill=(255, 255, 255, 240))
    img.save(output_image_path, "PNG")
    return output_image_path

def render_vertical_reel(
    raw_video_path: str,
    hook_text: str,
    output_filename: str,
    voiceover_path: Optional[str] = None,
    srt_path: Optional[str] = None
) -> Optional[str]:
    """
    Transforms raw video into a cinematic 9:16 vertical Reel:
    - Blurred background canvas (preserves 100% of sports action in center)
    - Centered crisp original foreground video
    - Top Hook banner
    - Bottom Watermark / Branding
    - AI Voiceover audio mixed cleanly with original video audio
    """
    ffmpeg_exe = get_ffmpeg_binary()
    output_path = str(PROCESSED_CLIPS_DIR / output_filename)
    
    # 1. Generate Overlay Images
    banner_img_path = str(TEMP_DIR / f"banner_{Path(output_filename).stem}.png")
    watermark_img_path = str(TEMP_DIR / f"watermark_{Path(output_filename).stem}.png")

    create_top_banner_image(hook_text, banner_img_path, width=TARGET_WIDTH, height=260)
    create_bottom_watermark_image(WATERMARK_TEXT, watermark_img_path, width=TARGET_WIDTH, height=100)

    # 2. Build FFmpeg command for Blurred Canvas
    inputs = [
        "-i", raw_video_path,
        "-i", banner_img_path,
        "-i", watermark_img_path
    ]

    # Cinematic Blurred Background + Centered Crisp Video
    video_filters = [
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg]",
        "[0:v]scale=1080:-2:force_original_aspect_ratio=decrease[fg]",
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]",
        "[base][1:v]overlay=0:120[with_banner]",
        "[with_banner][2:v]overlay=0:1700[outv]"
    ]

    # Audio handling: If voiceover exists, mix it with ducked original audio
    audio_map = []
    if voiceover_path and os.path.exists(voiceover_path):
        inputs.extend(["-i", voiceover_path])
        audio_filter = "[0:a]volume=0.25[orig_a];[3:a]volume=1.0[voice_a];[orig_a][voice_a]amix=inputs=2:duration=longest[outa]"
        filter_complex_str = ";".join(video_filters) + ";" + audio_filter
        audio_map = ["-map", "[outa]"]
    else:
        filter_complex_str = ";".join(video_filters)
        audio_map = ["-map", "0:a?"]

    cmd = [
        ffmpeg_exe, "-y",
        *inputs,
        "-filter_complex", filter_complex_str,
        "-map", "[outv]",
        *audio_map,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-shortest",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"[*] Rendering Cinematic Blurred-Canvas 9:16 Reel: {output_filename}...")
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            print(f"[-] FFmpeg error: {process.stderr}")
            return None

        # Clean up temporary overlay files
        for tmp in [banner_img_path, watermark_img_path]:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass

        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            print(f"[+] Rendered successfully: {output_path} ({round(os.path.getsize(output_path)/(1024*1024), 2)} MB)")
            return output_path
        return None

    except Exception as e:
        print(f"[-] Video processing failed: {e}")
        return None

if __name__ == "__main__":
    print(f"FFmpeg binary detected: {get_ffmpeg_binary()}")
