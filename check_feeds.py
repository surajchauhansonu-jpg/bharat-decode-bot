"""python check_feeds.py  -> kaun si feed chal rahi hai dikhata hai."""
import news
from config import FEEDS

for f in FEEDS:
    try:
        n = len(news.fetch_feed(f))
        print(f"OK   {n:3d} items  {f['name']}")
    except Exception as ex:
        print(f"FAIL {f['name']}: {ex}")
