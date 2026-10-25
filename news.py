import io
import re
from calendar import timegm
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from bs4 import BeautifulSoup
from PIL import Image

from config import FEEDS, MAX_AGE_HOURS, UA

HEADERS = {"User-Agent": UA, "Accept-Language": "hi-IN,hi;q=0.9,en;q=0.8"}


def _text(html):
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)


def _entry_image(e):
    for key in ("media_content", "media_thumbnail"):
        for m in e.get(key, []) or []:
            if m.get("url"):
                return m["url"]
    for enc in e.get("enclosures", []) or []:
        if (enc.get("type") or "").startswith("image") and enc.get("href"):
            return enc["href"]
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', e.get("summary", "") or "")
    return m.group(1) if m else None


def fetch_feed(feed):
    r = requests.get(feed["url"], headers=HEADERS, timeout=25)
    r.raise_for_status()
    parsed = feedparser.parse(r.content)
    out = []
    limit = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    for e in parsed.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")
        pub = datetime.fromtimestamp(timegm(t), tz=timezone.utc) if t else None
        if pub and pub < limit:
            continue
        link = e.get("link")
        title = _text(e.get("title"))
        if not link or not title:
            continue
        out.append({
            "title": title,
            "summary": _text(e.get("summary")),
            "link": link,
            "published": pub,
            "source": feed["name"],
            "region": feed["region"],
            "image": _entry_image(e),
        })
    return out


def collect():
    items, seen = [], set()
    for feed in FEEDS:
        try:
            for it in fetch_feed(feed):
                if it["link"] not in seen:
                    seen.add(it["link"])
                    items.append(it)
        except Exception as ex:  # ek feed fail ho to baaki chalte rahein
            print(f"[feed fail] {feed['name']}: {ex}")
    return items


def fetch_article(url):
    """(body_text, og_image_url) return karta hai."""
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    img = None
    for attrs in ({"property": "og:image"}, {"name": "twitter:image"}):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            img = tag["content"]
            break
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    body = " ".join(p for p in paras if len(p) > 40)[:3500]
    return body, img


def download_image(url, min_width=500):
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    if im.width < min_width:
        raise ValueError(f"image chhoti hai: {im.width}px")
    return im
