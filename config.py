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

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
FB_GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v21.0")

# RSS feeds. Jo feed na chale usko check_feeds.py se pakad ke badal dena.
# region: bihar / india / world / cricket  (bihar ko score mein bonus milta hai)
FEEDS = [
    # --- Bihar ke priority sources (aapke diye hue 5) ---
    {"name": "Live Hindustan Bihar", "region": "bihar", "priority": True,
     "url": "https://api.livehindustan.com/feeds/rss/bihar/rssfeed.xml"},
    {"name": "LiveCities", "region": "bihar", "priority": True,
     "url": "https://livecities.news/feed/"},
    {"name": "Kashish News", "region": "bihar", "priority": True,
     "url": "https://kashishnews.com/rssfeed"},
    {"name": "Aaj Tak", "region": "india",
     "url": "https://www.aajtak.in/rssfeeds/?id=home"},
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
    {"name": "Amar Ujala Cricket", "region": "cricket",
     "url": "https://www.amarujala.com/rss/cricket.xml"},
]


# Jin sites ki RSS nahi hai unka listing page scrape hota hai.
# link_re: article link ka pattern. date_group: URL mein date ho to uska group number.
PAGES = [
    {"name": "ETV Bharat Bihar", "region": "bihar", "priority": True,
     "url": "https://www.etvbharat.com/hi/bihar",
     "link_re": r"^https://www\.etvbharat\.com/hi/[!a-z-]+/[^/?#]+-[a-z]{2,4}\d{9,}/?$"},
    {"name": "Aaj Tak Bihar", "region": "bihar", "priority": True,
     "url": "https://www.aajtak.in/bihar",
     "link_re": r"^https://www\.aajtak\.in/bihar/story/[^/?#]+-\d{6,}-(\d{4}-\d{2}-\d{2})$",
     "date_group": 1},
]
