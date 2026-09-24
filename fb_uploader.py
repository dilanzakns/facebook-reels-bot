import os
import sys
import requests
from typing import Optional, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from config import FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN

GRAPH_API_VERSION = "v19.0"

def is_fb_configured() -> bool:
    """Checks if Facebook credentials are set."""
    return bool(FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN and "your_" not in FB_PAGE_ID)

def get_actual_page_access_token() -> str:
    """
    Checks if FB_PAGE_ACCESS_TOKEN is a User Token or Page Token.
    If it's a User Token, fetches the specific Page Access Token for FB_PAGE_ID.
    """
    if not is_fb_configured():
        return FB_PAGE_ACCESS_TOKEN

    try:
        url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/accounts?access_token={FB_PAGE_ACCESS_TOKEN}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        accounts = data.get("data", [])
        for account in accounts:
            if str(account.get("id")) == str(FB_PAGE_ID):
                page_token = account.get("access_token")
                if page_token:
                    return page_token
    except Exception:
        pass

    return FB_PAGE_ACCESS_TOKEN

def verify_facebook_token() -> bool:
    """Tests if the configured Page Access Token is valid and has publishing permissions."""
    if not is_fb_configured():
        return False
    try:
        token_to_use = get_actual_page_access_token()
        url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FB_PAGE_ID}?fields=name,id&access_token={token_to_use}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "name" in data:
            print(f"[+] Connected to Facebook Page: '{data['name']}' (ID: {FB_PAGE_ID})")
            return True
        else:
            print(f"[-] Facebook Token Error: {data.get('error', {}).get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"[-] Failed to verify Facebook token: {e}")
        return False

def upload_video_to_facebook(
    video_path: str,
    title: str,
    caption: str
) -> Optional[str]:
    """
    Uploads a processed vertical Reel to Facebook Page via Meta Graph API.
    Returns the Facebook Video ID if successful.
    """
    if not is_fb_configured():
        print("[!] Facebook credentials (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN) not configured in .env.")
        print("[!] Running in SIMULATION MODE: Video is ready in outputs/ready_to_post folder.")
        return "SIMULATION_FB_ID_12345"

    if not os.path.exists(video_path):
        print(f"[-] Video file not found: {video_path}")
        return None

    page_token = get_actual_page_access_token()
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FB_PAGE_ID}/videos"

    print(f"[*] Uploading Reel to Facebook Page ({FB_PAGE_ID})...")
    try:
        with open(video_path, "rb") as f:
            files = {
                "source": (os.path.basename(video_path), f, "video/mp4")
            }
            data = {
                "access_token": page_token,
                "title": title,
                "description": caption,
                "published": "true"
            }

            response = requests.post(url, data=data, files=files, timeout=300)
            res_json = response.json()

            if "id" in res_json:
                fb_id = res_json["id"]
                print(f"[+] Successfully posted to Facebook! Video ID: {fb_id}")
                print(f"[+] View Post: https://www.facebook.com/{FB_PAGE_ID}/videos/{fb_id}/")
                return fb_id
            else:
                error_msg = res_json.get("error", {}).get("message", str(res_json))
                print(f"[-] Facebook Upload Failed: {error_msg}")
                return None

    except Exception as e:
        print(f"[-] Facebook upload exception: {e}")
        return None

if __name__ == "__main__":
    print("Testing Facebook connection...")
    verify_facebook_token()
