import os

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

MAX_AGE_HOURS = 10
MAX_GEMINI_CHECKS = 6
WAIT_MINUTES = int(os.getenv("WAIT_MINUTES", "25"))
ACTIVE_FROM_HOUR = 6
ACTIVE_TO_HOUR = 23

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
FB_GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v21.0")

# RSS sources. Site-page fallbacks are configured below in SITE_PAGES.
FEEDS = [
    {
        "name": "Live Hindustan Bihar",
        "region": "bihar",
        "url": "https://api.livehindustan.com/feeds/rss/bihar/rssfeed.xml",
    },
    {
        "name": "Aaj Tak",
        "region": "india",
        "url": "https://www.aajtak.in/rssfeeds/?id=home",
    },
    {
        "name": "Live Hindustan National",
        "region": "india",
        "url": "https://api.livehindustan.com/feeds/rss/national/rssfeed.xml",
    },
    {
        "name": "ABP Live",
        "region": "india",
        "url": "https://www.abplive.com/home/feed",
    },
    {
        "name": "BBC Hindi",
        "region": "india",
        "url": "https://feeds.bbci.co.uk/hindi/rss.xml",
    },
    {
        "name": "Live Hindustan World",
        "region": "world",
        "url": "https://api.livehindustan.com/feeds/rss/international/rssfeed.xml",
    },
    {
        "name": "BBC Hindi World",
        "region": "world",
        "url": "https://feeds.bbci.co.uk/hindi/international/rss.xml",
    },
    {
        "name": "Live Hindustan Cricket",
        "region": "cricket",
        "url": "https://api.livehindustan.com/feeds/rss/sports/cricket/rssfeed.xml",
    },
    {
        "name": "Amar Ujala Cricket",
        "region": "cricket",
        "url": "https://www.amarujala.com/rss/cricket.xml",
    },
]

# Website/category pages: fallback collection when a reliable RSS feed is not configured.
# Page scraping is best-effort; articles without a detectable recent date are excluded
# by default to avoid accidentally reposting old stories.
SITE_PAGES = [
    {
        "name": "LiveCities Bihar",
        "region": "bihar",
        "url": "https://livecities.news/",
        "domains": ["livecities.news"],
    },
    {
        "name": "Kashish News Bihar",
        "region": "bihar",
        "url": "https://kashishnews.com/",
        "domains": ["kashishnews.com"],
    },
    {
        "name": "ETV Bharat Bihar",
        "region": "bihar",
        "url": "https://www.etvbharat.com/hi/bihar",
        "domains": ["etvbharat.com"],
    },
    {
        "name": "Live Hindustan Bihar page",
        "region": "bihar",
        "url": "https://www.livehindustan.com/bihar/news",
        "domains": ["livehindustan.com"],
    },
    {
        "name": "Aaj Tak Bihar page",
        "region": "bihar",
        "url": "https://www.aajtak.in/bihar",
        "domains": ["aajtak.in"],
    },
]
