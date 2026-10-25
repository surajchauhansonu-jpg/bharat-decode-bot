import requests

from config import FB_GRAPH_VERSION


def post_photo(page_id, token, jpg, caption):
    url = f"https://graph.facebook.com/{FB_GRAPH_VERSION}/{page_id}/photos"
    r = requests.post(url, timeout=120,
                      data={"access_token": token, "message": caption,
                            "published": "true"},
                      files={"source": ("poster.jpg", jpg, "image/jpeg")})
    data = r.json()
    if r.status_code != 200 or "error" in data:
        raise RuntimeError(f"Facebook error: {data}")
    return data
