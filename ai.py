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

नियम (पोस्टर में दो हिस्से हैं: बड़ा headline, और उसके नीचे एक डार्क बॉक्स वाली लाइन quote_line):

दो layout में से एक चुनो:
- layout "A" (नेता का दूसरे पर तंज/पलटवार/हमला जैसी ख़बर):
  headline: ज़्यादा से ज़्यादा 40 अक्षर, पोस्टर वाली ज़ुबान, अंत में ! या ?, जैसे "अनंत सिंह का नीरज कुमार पर तंज!"
  quote_line: "बोले- '...'" या "कहा- '...'" फ़ॉर्मेट, ज़्यादा से ज़्यादा 75 अक्षर, बयान सिर्फ़ ख़बर के असली शब्दों से। महिला नेता हों तो "बोलीं-"। (cricket में जहां बयान नहीं है, वहां एक लाइन में सबसे अहम तथ्य)
- layout "B" (जब ख़बर का असली दम नेता के सीधे, दमदार बयान में है):
  headline: उस बयान का सबसे दमदार हिस्सा, ख़बर के असली शब्दों में, ज़्यादा से ज़्यादा 65 अक्षर, उद्धरण चिह्न के बिना, जैसे "गद्दारों को कर्मों की सजा मिल रही है, बुरे कर्म का बुरा नतीजा"
  quote_line: कौन किस पर बोला, एक लाइन, ज़्यादा से ज़्यादा 45 अक्षर, शुरू में "-" के बिना, जैसे "RJD ने अनंत सिंह पर साधा निशाना" या "सम्राट चौधरी का कांग्रेस पर पलटवार"
- दोनों में quote गढ़ना मना है, सिर्फ़ ख़बर के असली शब्द।
- caption: 3-4 छोटी लाइनें देवनागरी में, तथ्य सही और निष्पक्ष, किसी पार्टी का पक्ष मत लो, गाली/अपशब्द नहीं। आख़िरी लाइन में पूछो/कहो कि आप क्या सोचते हैं (कमेंट में बताएं)।
- hashtags: 4 से 6, देवनागरी या अंग्रेज़ी, पहला हमेशा #Bharatdecode

सिर्फ़ यह JSON लौटाओ, और कुछ नहीं:
{{"skip": false, "skip_reason": "", "headline": "", "layout": "A", "quote_line": "", "caption": "", "hashtags": ["#Bharatdecode"]}}

ख़बर का स्रोत: {source}
क्षेत्र: {region}
शीर्षक: {title}
सारांश: {summary}
पूरा टेक्स्ट: {body}
"""


_state = {"cands": None, "dead": set()}
BASE = "https://generativelanguage.googleapis.com/v1beta"
SKIP_WORDS = ("image", "tts", "live", "audio", "thinking", "embedding", "exp",
              "robotics", "computer", "vision")


def _discover(key):
    """Key par jitne flash models available hain, stable pehle, naya pehle."""
    r = requests.get(f"{BASE}/models", params={"key": key, "pageSize": 200}, timeout=30)
    r.raise_for_status()
    names = []
    for m in r.json().get("models", []):
        n = m["name"].split("/")[-1]
        if ("generateContent" in m.get("supportedGenerationMethods", [])
                and "flash" in n and not any(x in n for x in SKIP_WORDS)):
            names.append(n)
    stable = sorted([n for n in names if "preview" not in n], reverse=True)
    prev = sorted([n for n in names if "preview" in n], reverse=True)
    return stable + prev


def _candidates(key):
    order = [GEMINI_MODEL, "gemini-flash-lite-latest"]
    try:
        found = _discover(key)
        print("  available flash models:", ", ".join(found[:8]) or "koi nahi")
        # lite models bhi fallback mein rakho (free limit zyada hoti hai)
        order += [n for n in found if "lite" in n] + found
    except Exception as ex:
        print("  models list fail:", ex)
    out = []
    for n in order:
        if n and n not in out:
            out.append(n)
    return out[:5]


def _call(prompt):
    key = os.environ["GEMINI_API_KEY"]
    if _state["cands"] is None:
        _state["cands"] = _candidates(key)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4,
                                 "responseMimeType": "application/json"}}
    last = "koi model try nahi hua"
    for model in list(_state["cands"]):
        if model in _state["dead"]:
            continue
        for attempt in range(2):
            try:
                r = requests.post(f"{BASE}/models/{model}:generateContent?key={key}",
                                  json=body, timeout=45)
            except requests.RequestException as ex:
                last = f"{model}: {type(ex).__name__}"
                print(f"  {last}")
                break  # timeout/connection: agle model par jao
            if r.status_code == 404:
                _state["dead"].add(model)
                last = f"{model}: 404"
                print(f"  {last} (model nahi mila)")
                break
            if r.status_code in (429, 500, 503):
                last = f"{model}: HTTP {r.status_code} {r.text[:250]}"
                print(f"  {last}")
                if attempt == 0:
                    time.sleep(8)
                    continue
                break
            if r.status_code >= 400:
                last = f"{model}: HTTP {r.status_code} {r.text[:250]}"
                print(f"  {last}")
                break
            data = r.json()
            cands = data.get("candidates") or []
            if not cands or "content" not in cands[0] or not cands[0]["content"].get("parts"):
                return {"skip": True, "skip_reason": "Gemini ne content block kiya"}
            if _state["cands"][0] != model:  # chalne wala model aage rakho
                _state["cands"].remove(model)
                _state["cands"].insert(0, model)
                print(f"  ab '{model}' use ho raha hai")
            txt = cands[0]["content"]["parts"][0]["text"]
            txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
            return json.loads(txt)
    raise RuntimeError(f"Gemini sab models par fail. Last: {last}")


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
    d["layout"] = "B" if str(d.get("layout", "A")).strip().upper() == "B" else "A"
    if d["layout"] == "B":
        d["headline"] = d["headline"].strip().strip("\"'‘’“”")
        ql = d["quote_line"].strip().lstrip("-–— ").strip()
        d["quote_line"] = "- " + ql
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
