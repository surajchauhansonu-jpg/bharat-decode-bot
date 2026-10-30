import io
import re
from urllib.parse import urljoin
from calendar import timegm
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from bs4 import BeautifulSoup
from PIL import Image

from config import FEEDS, MAX_AGE_HOURS, PAGES, UA

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
            "priority": bool(feed.get("priority")),
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
    for page in PAGES:
        try:
            for it in fetch_page(page):
                if it["link"] not in seen:
                    seen.add(it["link"])
                    items.append(it)
        except Exception as ex:
            print(f"[page fail] {page['name']}: {ex}")
    return items


def fetch_page(page):
    """Listing page se article links nikalo (jin sites ki RSS nahi hai)."""
    r = requests.get(page["url"], headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rx = re.compile(page["link_re"])
    found, sample = {}, []
    for a in soup.find_all("a", href=True):
        url = urljoin(page["url"], a["href"]).split("#")[0]
        if len(sample) < 6 and url.startswith("http"):
            sample.append(url)
        m = rx.match(url)
        if not m:
            continue
        text = a.get_text(" ", strip=True) or a.get("title") or ""
        if not text:
            img = a.find("img")
            text = (img.get("alt") if img else "") or ""
        text = re.sub(r"\s*-?\s*VIDEO\s*$", "", text.strip())
        if url not in found or len(text) > len(found[url][0]):
            found[url] = (text, m)
    if not found:
        print(f"[page] {page['name']}: koi link match nahi hua. Pattern check karo. "
              f"Page ke kuch links: {sample}")
    out = []
    limit_day = (datetime.now(timezone.utc) - timedelta(days=2)).date()
    for url, (text, m) in list(found.items())[:30]:
        if len(text) < 15:
            continue
        pub = None
        if page.get("date_group"):
            try:
                y, mo, d = (int(x) for x in m.group(page["date_group"]).split("-"))
                pub = datetime(y, mo, d, tzinfo=timezone.utc)
                if pub.date() < limit_day:  # 2 din se purani URL-date skip
                    continue
            except Exception:
                pub = None
        out.append({"title": text, "summary": "", "link": url, "published": pub,
                    "source": page["name"], "region": page["region"],
                    "priority": bool(page.get("priority")), "image": None})
    return out


def fetch_article(url):
    """(body_text, og_image_url, extra) return karta hai.
    extra = {"keywords": [...], "description": "..."}"""
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    def meta(**attrs):
        tag = soup.find("meta", attrs=attrs)
        return (tag.get("content") or "").strip() if tag else ""

    img = meta(property="og:image") or meta(name="twitter:image") or None
    desc = meta(property="og:description") or meta(name="description")
    kws = []
    for raw in (meta(name="keywords"), meta(name="news_keywords")):
        kws += [k.strip() for k in raw.split(",")]
    for tag in soup.find_all("meta", attrs={"property": "article:tag"}):
        kws.append((tag.get("content") or "").strip())
    seen_k, keywords = set(), []
    for k in kws:
        if 2 <= len(k) <= 30 and k.lower() not in seen_k:
            seen_k.add(k.lower())
            keywords.append(k)
    paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    body = " ".join(p for p in paras if len(p) > 40)[:3500]
    if len(body) < 300 and desc:
        body = (desc + " " + body).strip()
    return body, img, {"keywords": keywords[:12], "description": desc}


# ---------- ek hi khabar kai sources par: related aur duplicate ----------
_STOP = {"के", "की", "का", "में", "से", "पर", "ने", "को", "और", "है", "हैं", "भी",
         "एक", "ही", "तो", "इस", "जो", "कि", "ये", "वो", "अब", "बड़ा", "बड़ी", "news"}


def _toks(s):
    return {t for t in re.findall(r"[\u0900-\u097Fa-zA-Z0-9]+", (s or "").lower())
            if len(t) > 1 and t not in _STOP}


def _overlap(a, b):
    if not a or not b:
        return 0, 0.0
    c = len(a & b)
    return c, c / min(len(a), len(b))


def find_related(item, items, k=2):
    """Doosre sources ki wahi khabar (title milta-julta)."""
    a = _toks(item["title"])
    scored = []
    for o in items:
        if o["link"] == item["link"] or o["source"] == item["source"]:
            continue
        c, ratio = _overlap(a, _toks(o["title"]))
        if c >= 3 and ratio >= 0.5:
            scored.append((ratio, o))
    scored.sort(key=lambda x: x[0], reverse=True)
    seen_src, out = set(), []
    for _, o in scored:
        if o["source"] not in seen_src:
            seen_src.add(o["source"])
            out.append(o)
    return out[:k]


def is_duplicate(title, old_titles):
    """Pehle post/check ho chuki khabar ka naya source to nahi?"""
    a = _toks(title)
    for t in old_titles:
        c, ratio = _overlap(a, _toks(t))
        if c >= 4 and ratio >= 0.6:
            return True
    return False


def download_image(url, min_width=500):
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    if im.width < min_width:
        raise ValueError(f"image chhoti hai: {im.width}px")
    return im
