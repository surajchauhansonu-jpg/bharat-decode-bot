"""Inset photo: pehle apni library (assets/people), phir Wikipedia."""
import io
import os
import re

import requests
from PIL import Image

from config import UA

BASE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(BASE, "assets", "people")
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def _tokens(s):
    return {t for t in re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split() if t}


def from_library(name):
    q = _tokens(name)
    if not q or not os.path.isdir(LIB):
        return None
    best, best_n = None, 0
    for f in os.listdir(LIB):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in EXTS:
            continue
        t = _tokens(stem)
        ok = bool(t) and (t <= q or (q <= t and len(q) >= 2))
        if ok and len(t & q) > best_n:
            best, best_n = f, len(t & q)
    if not best:
        return None
    return Image.open(os.path.join(LIB, best)).convert("RGB"), f"library: {best}"


def from_wikipedia(name):
    q = _tokens(name)
    if len(q) < 2:
        return None
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php", timeout=20,
                         headers={"User-Agent": UA},
                         params={"action": "query", "format": "json", "generator": "search",
                                 "gsrsearch": f"{name} Indian politician", "gsrlimit": 3,
                                 "prop": "pageimages", "piprop": "thumbnail",
                                 "pithumbsize": 800})
        pages = (r.json().get("query") or {}).get("pages") or {}
        for pg in sorted(pages.values(), key=lambda p: p.get("index", 99)):
            src = (pg.get("thumbnail") or {}).get("source")
            # naam ke saare shabd page title mein hon, warna galat insaan ho sakta hai
            if src and q <= _tokens(pg.get("title", "")):
                img = requests.get(src, timeout=20, headers={"User-Agent": UA})
                img.raise_for_status()
                return Image.open(io.BytesIO(img.content)).convert("RGB"), \
                    f"wikipedia: {pg['title']}"
    except Exception as ex:
        print("  wikipedia fail:", ex)
    return None


def find(name):
    """(PIL image ya None, source text) return karta hai."""
    if not name or not str(name).strip():
        return None, "koi naam nahi"
    for fn in (from_library, from_wikipedia):
        try:
            res = fn(name)
        except Exception as ex:
            print(f"  {fn.__name__} fail:", ex)
            res = None
        if res:
            return res
    return None, f"'{name}' ki photo nahi mili"
