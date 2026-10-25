import json
import os
import re
import time

import requests

from config import GEMINI_MODEL
from filters import blocked_reason

PROMPT = """तुम "Bharat Decode" नाम के हिंदी न्यूज़ फेसबुक पेज के एडिटर हो। पेज बिहार की ब्रेकिंग न्यूज़ और भारत/दुनिया की अहम ख़बरें डालता है, ख़ासकर तब जब किसी नेता ने कोई नया बयान दिया हो।

पेज क्रिकेट की ख़बरें भी डालता है (क्षेत्र = cricket)।

नीचे एक ख़बर है। फ़ैसला करो कि इस पर पोस्ट बनानी है या नहीं, और बनानी है तो ड्राफ्ट लिखो।

SKIP करो (skip=true) अगर:
- ख़बर रेप, यौन हिंसा, यौन शोषण, छेड़छाड़, POCSO या ऐसे किसी अपराध से जुड़ी है (ज़रा सा भी संबंध हो तो skip)
- (क्षेत्र cricket को छोड़कर) ख़बर में किसी नामी नेता/मंत्री/सरकारी पद वाले व्यक्ति का साफ़ बयान नहीं है
- (सिर्फ़ cricket) ख़बर मामूली है: घरेलू/लोकल मैच की छोटी अपडेट, सिर्फ़ स्कोरकार्ड, या प्रीव्यू। बड़ी ख़बर ही लो: भारतीय टीम/बड़े खिलाड़ी/कप्तान/कोच/BCCI/ICC का बयान या फ़ैसला, स्क्वाड ऐलान, संन्यास, बड़े मैच या सीरीज़ का नतीजा, रिकॉर्ड, विवाद
- ख़बर अफ़वाह जैसी है, या सांप्रदायिक नफ़रत भड़का सकती है, या किसी की मौत/हादसे की ग्राफिक डिटेल है
- बयान ख़बर के टेक्स्ट में साफ़ नहीं मिल रहा

नियम:
- headline: ज़्यादा से ज़्यादा 40 अक्षर, पोस्टर वाली ज़ुबान, अंत में ! या ?, जैसे "अनंत सिंह का नीरज कुमार पर तंज!"
- quote_line: अगर बयान है तो "बोले- '...'" या "कहा- '...'" फ़ॉर्मेट। (सिर्फ़ cricket में, जहां बयान नहीं है, वहां एक लाइन में सबसे अहम तथ्य लिखो, जैसे "भारत ने सीरीज़ 3-1 से जीती"। तथ्य ख़बर से ही लो।) ज़्यादा से ज़्यादा 75 अक्षर। बयान सिर्फ़ ख़बर के असली शब्दों से लो, अपनी तरफ़ से कुछ मत जोड़ो, quote मत गढ़ो। महिला नेता हों तो "बोलीं-"।
- caption: 3-4 छोटी लाइनें देवनागरी में, तथ्य सही और निष्पक्ष, किसी पार्टी का पक्ष मत लो, गाली/अपशब्द नहीं। आख़िरी लाइन में पूछो/कहो कि आप क्या सोचते हैं (कमेंट में बताएं)।
- hashtags: 4 से 6, देवनागरी या अंग्रेज़ी, पहला हमेशा #Bharatdecode

सिर्फ़ यह JSON लौटाओ, और कुछ नहीं:
{{"skip": false, "skip_reason": "", "headline": "", "quote_line": "", "caption": "", "hashtags": ["#Bharatdecode"]}}

ख़बर का स्रोत: {source}
क्षेत्र: {region}
शीर्षक: {title}
सारांश: {summary}
पूरा टेक्स्ट: {body}
"""


def _call(prompt):
    key = os.environ["GEMINI_API_KEY"]
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={key}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4,
                                 "responseMimeType": "application/json"}}
    for attempt in range(3):
        r = requests.post(url, json=body, timeout=90)
        if r.status_code in (429, 503):
            time.sleep(20 * (attempt + 1))
            continue
        r.raise_for_status()
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
        return json.loads(txt)
    raise RuntimeError("Gemini busy/rate-limited")


def make_draft(item, body):
    """Draft dict return karta hai, ya None agar skip karna hai."""
    prompt = PROMPT.format(source=item["source"], region=item["region"],
                           title=item["title"], summary=item["summary"][:600],
                           body=body[:2800])
    d = _call(prompt)
    if d.get("skip"):
        print(f"  Gemini skip: {d.get('skip_reason')}")
        return None
    for k in ("headline", "quote_line", "caption"):
        if not str(d.get(k, "")).strip():
            print(f"  Gemini output mein '{k}' khali")
            return None
    out_text = " ".join([d["headline"], d["quote_line"], d["caption"]])
    hit = blocked_reason(out_text)
    if hit:
        print(f"  output mein blocked shabd: {hit}")
        return None

    tags = ["#Bharatdecode"]
    for t in d.get("hashtags", []):
        t = "#" + str(t).strip().lstrip("#").replace(" ", "")
        if len(t) > 1 and t.lower() not in [x.lower() for x in tags]:
            tags.append(t)
    d["hashtags"] = tags[:6]
    d["full_caption"] = (f"{d['caption'].strip()}\n\n{' '.join(d['hashtags'])}"
                         f"\n\nस्रोत: {item['source']}")
    return d
