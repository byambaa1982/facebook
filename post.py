import os
import requests
import json

# Load config from file or environment variables
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    PAGE_ID = config["page_id"]
    PAGE_TOKEN = config["page_token"]
except FileNotFoundError:
    # Fallback to environment variables or hardcoded values
    PAGE_ID = os.getenv("FB_PAGE_ID", "682084288324866")
    PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "EAAMU4HhUxE4BPTXZBIWzyKDlfk1lXtBvTKo6oUwezslEMc3uCAdEN5h8Tk6mLvNt3ZCKrrRN62vBdJmsCSFpv3ZC1W7uFrbbSmSlDktpbMPgNF6uUVOuIVIITahOOq2WMr0KUi1A40ilWkT6gCyZCjiVZBoZCQnPD5t5rt5TWBNg8KxoYDurqmxBVfxV8ZBOzaPJoxsLadpev25fpOTE5bR")

GRAPH = "https://graph.facebook.com/v21.0"

def _handle(r):
    try:
        r.raise_for_status()
        return r.json()
    except requests.HTTPError:
        # Pretty-print Graph API error
        try:
            print("ERROR:", r.json())
        except Exception:
            print("ERROR (raw):", r.text)
        raise

def post_text(message: str) -> str:
    """Create a text post on the Page. Requires pages_manage_posts + pages_read_engagement."""
    url = f"{GRAPH}/{PAGE_ID}/feed"
    r = requests.post(url, data={"message": message, "access_token": PAGE_TOKEN})
    data = _handle(r)
    post_id = data.get("id")
    print("Posted:", post_id)
    return post_id

def post_photo(image_url: str, caption: str = "") -> str:
    """Post a photo from a local file."""
    url = f"{GRAPH}/{PAGE_ID}/photos"
    with open(image_url, "rb") as img_file:
        r = requests.post(
            url,
            data={
                "caption": caption,
                "access_token": PAGE_TOKEN
            },
            files={"source": img_file}
        )
    data = _handle(r)
    photo_id = data.get("post_id") or data.get("id")
    print("Photo posted:", photo_id)
    return photo_id

def list_recent_posts(limit: int = 5):
    """List recent posts with permalink."""
    url = f"{GRAPH}/{PAGE_ID}/posts"
    r = requests.get(url, params={
        "fields": "id,message,created_time,permalink_url,status_type",
        "limit": limit,
        "access_token": PAGE_TOKEN
    })
    data = _handle(r)
    for item in data.get("data", []):
        print(f"- {item.get('id')} | {item.get('created_time')} | {item.get('permalink_url')}")
    return data

def delete_object(object_id: str) -> bool:
    """Delete a post/photo created by the app."""
    url = f"{GRAPH}/{object_id}"
    r = requests.delete(url, params={"access_token": PAGE_TOKEN})
    data = _handle(r)
    ok = data is True or data.get("success") is True
    print("Deleted:", object_id, ok)
    return ok

if __name__ == "__main__":
    # EXAMPLES: uncomment what you need

    # 1) Text post
    # post_id = post_text("Hello from Python 🐍 via Graph API!")

    # 2) Photo post (by URL)
    post_id = post_photo(
        image_url="duckdb.png",
        caption="Photo posted via Python"
    )

    # 3) List latest posts
    # list_recent_posts(limit=5)

    # 4) Delete a post you just created
    # delete_object(post_id)
    pass
