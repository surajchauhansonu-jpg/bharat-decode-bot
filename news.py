import io
import re
from calendar import timegm
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse, urldefrag

import feedparser
import requests
from bs4 import BeautifulSoup
from PIL import Image

from config import FEEDS, SITE_PAGES, MAX_AGE_HOURS, UA

HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "hi-IN,hi;q=0.9,en;q=0.8",
}
DATE_META_SELECTORS = [
    ("meta", {"property": "article:published_time"}),
    ("meta", {"name": "pubdate"}),
    ("meta", {"name": "publish-date"}),
    ("meta", {"name": "date"}),
    ("meta", {"itemprop": "datePublished"}),
]


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
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)", e.get("summary", "") or "")
    return m.group(1) if m else None


def _parse_datetime(value):
    if not value:
        return None
    value = value.strip()
    try:
        # ISO strings including timezone and trailing Z
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y %H:%M",
        "%d %B %Y %H:%M",
        "%d %b, %Y",
        "%d %B, %Y",
    ):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _within_age(pub):
    # If a feed provides no publication date, let it through only on RSS sources;
    # site-page results are handled more strictly in scrape_site_page().
    if not pub:
        return True
    return pub >= datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)


def fetch_feed(feed):
    r = requests.get(feed["url"], headers=HEADERS, timeout=25)
    r.raise_for_status()
    parsed = feedparser.parse(r.content)
    out = []
    for e in parsed.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")
        pub = datetime.fromtimestamp(timegm(t), tz=timezone.utc) if t else None
        if not _within_age(pub):
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


def _same_allowed_domain(url, domains):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in domains)


def _card_date(card):
    # Look for semantic date fields first, then visible time text.
    for tag in card.select("time[datetime], [itemprop='datePublished'], [data-date]"):
        raw = tag.get("datetime") or tag.get("content") or tag.get("data-date") or tag.get_text(" ", strip=True)
        dt = _parse_datetime(raw)
        if dt:
            return dt
    text = card.get_text(" ", strip=True)
    # Common English date formats, e.g. 28 Oct 2026 / October 28, 2026
    patterns = [
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}(?:[, ]+\d{1,2}:\d{2}\s*(?:AM|PM)?)?\b",
        r"\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}(?:[, ]+\d{1,2}:\d{2}\s*(?:AM|PM)?)?\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            dt = _parse_datetime(m.group(0))
            if dt:
                return dt
    return None


def scrape_site_page(site):
    """Best-effort collection from a site's category/home page.
    Only links with a detectable recent date are accepted to reduce stale stories.
    """
    r = requests.get(site["url"], headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    results, local_seen = [], set()

    for a in soup.find_all("a", href=True):
        href = urljoin(site["url"], a["href"])
        href = urldefrag(href)[0]
        if not _same_allowed_domain(href, site["domains"]):
            continue
        parsed = urlparse(href)
        path = parsed.path.strip("/")
        if not path or any(path.lower().endswith(ext) for ext in (
            ".jpg", ".jpeg", ".png", ".webp", ".svg", ".pdf", ".mp4"
        )):
            continue
        if href in local_seen:
            continue

        title = _text(a.get_text(" ", strip=True))
        if len(title) < 18 or len(title) > 220:
            continue
        if title.lower() in {"read more", "और पढ़ें", "और पढ़ें", "देखें", "live tv"}:
            continue

        # Prefer a card/article container near the link, not the whole page.
        card = a
        for parent in a.parents:
            if parent.name in ("article", "li"):
                card = parent
                break
            if parent.name in ("div", "section") and parent.find(["h2", "h3"]):
                card = parent
                break
            if parent.name in ("body", "html"):
                break

        pub = _card_date(card)
        # Strict freshness: skip page results when no publication date is available.
        if not pub or pub < cutoff:
            continue

        summary = _text(card.get_text(" ", strip=True))
        if summary == title:
            summary = ""
        img = card.find("img")
        image = None
        if img:
            image = img.get("src") or img.get("data-src") or img.get("data-original")
            if image:
                image = urljoin(site["url"], image)

        local_seen.add(href)
        results.append({
            "title": title,
            "summary": summary[:900],
            "link": href,
            "published": pub,
            "source": site["name"],
            "region": site["region"],
            "image": image,
        })
    return results


def collect():
    items, seen = [], set()
    for feed in FEEDS:
        try:
            for it in fetch_feed(feed):
                if it["link"] not in seen:
                    seen.add(it["link"])
                    items.append(it)
        except Exception as ex:
            print(f"[feed fail] {feed['name']}: {ex}")

    for site in SITE_PAGES:
        try:
            found = scrape_site_page(site)
            print(f"[site page] {site['name']}: {len(found)} recent dated items")
            for it in found:
                if it["link"] not in seen:
                    seen.add(it["link"])
                    items.append(it)
        except Exception as ex:
            print(f"[site scrape fail] {site['name']}: {ex}")
    return items


def fetch_article(url):
    """Return (body_text, og_image_url)."""
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    img = None
    for attrs in ({"property": "og:image"}, {"name": "twitter:image"}):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            img = urljoin(url, tag["content"])
            break

    # Prefer likely article body containers before falling back to all paragraphs.
    containers = soup.select(
        "article, [itemprop='articleBody'], .article-content, .story-content, "
        ".story__content, .article-body, .news-detail, .content-area"
    )
    paras = []
    for container in containers:
        candidate = [
            p.get_text(" ", strip=True)
            for p in container.find_all("p")
            if len(p.get_text(" ", strip=True)) > 35
        ]
        if sum(map(len, candidate)) > 250:
            paras = candidate
            break

    if not paras:
        paras = [
            p.get_text(" ", strip=True)
            for p in soup.find_all("p")
            if len(p.get_text(" ", strip=True)) > 40
        ]

    body = " ".join(paras)[:3500]
    if len(body) < 120:
        raise ValueError("Article text bahut kam mila; AI ko adhuri khabar nahi bheji")
    return body, img


def download_image(url, min_width=500):
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    if im.width < min_width:
        raise ValueError(f"image chhoti hai: {im.width}px")
    return im
