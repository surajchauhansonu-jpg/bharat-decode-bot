"""Rape/sexual-violence filter + 'leader ka bayan' scoring."""
import re

DEV = "\u0900-\u097F"

# Ye shabd kahin bhi mile (substring) -> news skip
BLOCK_SUBSTR = [
    "बलात्कार", "दुष्कर्म", "गैंगरेप", "गैंग रेप", "गैंग-रेप", "दुराचार",
    "यौन शोषण", "यौन उत्पीड़न", "यौन हिंसा",
    "छेड़खानी", "दरिंदगी", "हवस", "आबरू", "अस्मत", "इज्जत लूट", "इज़्ज़त लूट",
    "अश्लील हरकत", "सामूहिक रेप",
]
# "रेप" akela shabd regex se pakadte hain (substring se "रेपो रेट" bhi ruk jata)
BLOCK_REGEX = [
    re.compile(rf"(?<![{DEV}])(रेप|रेपिस्ट|रेपी)(?![{DEV}])"),
    re.compile(r"\b(rape[sd]?|rapists?|gang-?rape[sd]?|molest\w*|pocso|"
               r"sexual(ly)? (assault\w*|abus\w*|harass\w*|exploit\w*)|"
               r"sex scandal|sex racket)\b", re.I),
]
# Ye combo ek saath aaye tabhi block (taaki "EVM se chhedchhad" jaisi news na ruke)
COMBO_A = ["छेड़छाड़", "छेड़-छाड़", "अश्लील", "अभद्र", "शारीरिक शोषण"]
COMBO_B = ["छात्रा", "युवती", "महिला", "लड़की", "बच्ची", "नाबालिग", "किशोरी",
           "बालिका", "नर्स", "शिक्षिका", "बहू"]


def blocked_reason(text: str):
    """Agar text mein sensitive cheez hai to wo shabd return karega, warna None."""
    if not text:
        return None
    t = text.lower()
    for w in BLOCK_SUBSTR:
        if w in t:
            return w
    for rx in BLOCK_REGEX:
        m = rx.search(text)
        if m:
            return m.group(0)
    if any(a in t for a in COMBO_A) and any(b in t for b in COMBO_B):
        return "छेड़छाड़/अश्लील + महिला/नाबालिग"
    return None


STATEMENT_WORDS = [
    "बोले", "बोलीं", "बोला", "बयान", "तंज", "पलटवार", "निशाना", "हमला", "कहा",
    "चुनौती", "आरोप", "जवाब", "सफाई", "नसीहत", "चेतावनी", "दावा", "ऐलान",
    "अपील", "प्रतिक्रिया", "बरसे", "भड़के", "घेरा", "सलाह", "ताना", "भविष्यवाणी",
]
LEADERS = [
    "नीतीश", "तेजस्वी", "तेज प्रताप", "सम्राट चौधरी", "विजय सिन्हा", "चिराग",
    "पशुपति पारस", "मांझी", "कुशवाहा", "पप्पू यादव", "प्रशांत किशोर", "पीके",
    "लालू", "राबड़ी", "मीसा", "रविशंकर", "गिरिराज", "अनंत सिंह", "मोदी",
    "अमित शाह", "राहुल गांधी", "प्रियंका", "खड़गे", "योगी", "केजरीवाल", "ममता",
    "अखिलेश", "ओवैसी", "राजनाथ", "नड्डा", "जयशंकर", "भागवत", "ट्रंप", "पुतिन",
    "नेतन्याहू", "जिनपिंग", "शहबाज", "जेलेंस्की", "सुशील मोदी", "संजय झा",
    "मंगल पांडेय", "नित्यानंद राय", "शाहनवाज", "आरसीपी", "पवन सिंह",
]
CRICKET_PEOPLE = [
    "कोहली", "रोहित", "धोनी", "बुमराह", "गिल", "पंत", "जडेजा", "अश्विन", "सूर्यकुमार",
    "हार्दिक", "राहुल द्रविड़", "गंभीर", "अगरकर", "जय शाह", "BCCI", "बीसीसीआई",
    "आईसीसी", "ICC", "कपिल देव", "सचिन", "गांगुली", "शास्त्री", "सिराज", "शमी",
    "वैभव सूर्यवंशी", "पाटीदार", "श्रेयस", "ईशान", "जायसवाल", "बाबर", "रिजवान",
    "कमिंस", "स्मिथ", "स्टोक्स", "रूट",
]
CRICKET_WORDS = ["क्रिकेट", "टेस्ट", "वनडे", "T20", "टी20", "आईपीएल", "IPL", "विश्व कप",
                 "वर्ल्ड कप", "एशिया कप", "रणजी", "कप्तान", "कोच", "संन्यास", "टीम इंडिया",
                 "भारत बनाम", "जीत", "हार", "शतक", "विकेट", "सीरीज", "स्क्वाड", "चयन"]
ROLES = ["मुख्यमंत्री", "प्रधानमंत्री", "उपमुख्यमंत्री", "डिप्टी सीएम", "मंत्री",
         "सांसद", "विधायक", "अध्यक्ष", "नेता प्रतिपक्ष", "राष्ट्रपति", "सीएम",
         "पूर्व मंत्री", "प्रवक्ता"]


def score(item: dict) -> int:
    title = item["title"]
    s = 0
    if any(w in title for w in STATEMENT_WORDS):
        s += 3
    if any(l in title for l in LEADERS):
        s += 3
    if any(r in title for r in ROLES):
        s += 1
    if any(q in title for q in ("‘", "’", '"', "“", "”")):
        s += 2
    if item["region"] == "bihar":
        s += 2
    if item["region"] == "cricket":
        # cricket mein bayan zaroori nahi: bada player/board + cricket keyword kaafi hai
        if any(p in title for p in CRICKET_PEOPLE):
            s += 3
        if any(w in title for w in CRICKET_WORDS):
            s += 1
    return s
