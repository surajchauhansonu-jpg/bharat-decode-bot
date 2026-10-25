import os

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Kitne ghante purani news tak lena hai
MAX_AGE_HOURS = 10
# Ek run mein max kitne article Gemini se check karne hain
MAX_GEMINI_CHECKS = 6
# Telegram par approve ka wait (minutes)
WAIT_MINUTES = int(os.getenv("WAIT_MINUTES", "25"))
# Bot sirf is time-window mein chalega (IST)
ACTIVE_FROM_HOUR = 6
ACTIVE_TO_HOUR = 23

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FB_GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v21.0")

# RSS feeds. Jo feed na chale usko check_feeds.py se pakad ke badal dena.
# region: bihar / india / world / cricket  (bihar ko score mein bonus milta hai)
FEEDS = [
    {"name": "Live Hindustan Bihar", "region": "bihar",
     "url": "https://api.livehindustan.com/feeds/rss/bihar/rssfeed.xml"},
    {"name": "News18 Bihar", "region": "bihar",
     "url": "https://hindi.news18.com/commonfeeds/v1/hin/rss/bihar.xml"},
    {"name": "Amar Ujala Bihar", "region": "bihar",
     "url": "https://www.amarujala.com/rss/bihar.xml"},
    {"name": "Aaj Tak", "region": "india",
     "url": "https://www.aajtak.in/rssfeeds/?id=home"},
    {"name": "NDTV India", "region": "india",
     "url": "https://khabar.ndtv.com/rss"},
    {"name": "Live Hindustan National", "region": "india",
     "url": "https://api.livehindustan.com/feeds/rss/national/rssfeed.xml"},
    {"name": "ABP Live", "region": "india",
     "url": "https://www.abplive.com/home/feed"},
    {"name": "BBC Hindi", "region": "india",
     "url": "https://feeds.bbci.co.uk/hindi/rss.xml"},
    {"name": "Live Hindustan World", "region": "world",
     "url": "https://api.livehindustan.com/feeds/rss/international/rssfeed.xml"},
    {"name": "BBC Hindi World", "region": "world",
     "url": "https://feeds.bbci.co.uk/hindi/international/rss.xml"},
    # Cricket
    {"name": "Live Hindustan Cricket", "region": "cricket",
     "url": "https://api.livehindustan.com/feeds/rss/sports/cricket/rssfeed.xml"},
    {"name": "Aaj Tak Cricket", "region": "cricket",
     "url": "https://www.aajtak.in/rssfeeds/?id=cricket"},
    {"name": "News18 Cricket", "region": "cricket",
     "url": "https://hindi.news18.com/commonfeeds/v1/hin/rss/cricket.xml"},
    {"name": "Amar Ujala Cricket", "region": "cricket",
     "url": "https://www.amarujala.com/rss/cricket.xml"},
]
