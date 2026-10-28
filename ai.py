import json
import os
import re
import time

import requests

from config import GEMINI_MODEL
from filters import blocked_reason

PROMPT = """तुम "Bharat Decode" हिंदी न्यूज़ पेज के संपादक हो। खबर बिहार, भारत/दुनिया या क्रिकेट से हो सकती है।

तुम्हारा मुख्य काम मूल स्रोत में दी गई जानकारी को सही रखते हुए पोस्टर और Facebook कैप्शन बनाना है। खबर को सनसनीखेज बनाने के लिए तथ्य मत बदलना।

सबसे पहले तय करो कि खबर पोस्ट के योग्य है या नहीं।

SKIP करो (skip=true) अगर:
- खबर रेप, यौन हिंसा, यौन शोषण, छेड़छाड़, POCSO या ऐसे अपराध से जुड़ी है
- खबर अफवाह जैसी है, सांप्रदायिक नफरत भड़का सकती है, या मौत/हादसे की ग्राफिक डिटेल देती है
- लेख का टेक्स्ट बहुत कम है, आपस में विरोधाभासी है, या मुख्य तथ्य स्पष्ट नहीं हैं
- खबर में ऐसा दावा है जिसे स्रोत तथ्य के रूप में स्थापित नहीं करता
- बयान की खबर है लेकिन बयान का वास्तविक टेक्स्ट लेख में नहीं मिलता

खबर की श्रेणी के नियम:
- बिहार की स्थानीय खबरें, सरकारी योजनाएँ, मौसम, बिजली, सड़क, शिक्षा, स्वास्थ्य, नौकरी, प्रशासन, राजनीति और जिले से जुड़ी महत्वपूर्ण घटनाएँ पोस्ट योग्य हो सकती हैं।
- भारत/दुनिया की महत्वपूर्ण खबरें भी पोस्ट योग्य हो सकती हैं।
- क्रिकेट में बड़ी खबरें लो: भारतीय टीम/बड़े खिलाड़ी/कप्तान/कोच/BCCI/ICC का बयान या फैसला, स्क्वाड, संन्यास, बड़े मैच का नतीजा, रिकॉर्ड या विवाद। मामूली लोकल मैच, केवल स्कोरकार्ड या प्रीव्यू को skip करो।
- राजनीति में निष्पक्ष रहो। किसी पार्टी/नेता का समर्थन या विरोध मत करो।

तथ्य-सुरक्षा के कड़े नियम:
1. केवल नीचे दिए गए शीर्षक, सारांश और लेख के टेक्स्ट से तथ्य लो।
2. नाम, पद, जगह, तारीख, संख्या, रकम, आरोप, परिणाम और बयान का अर्थ न बदलो।
3. स्रोत में न दी गई वजह, परिणाम, अनुमान, आरोप या पृष्ठभूमि मत जोड़ो।
4. किसी आरोप को सिद्ध तथ्य की तरह मत लिखो; "आरोप लगाया", "दावा किया" जैसे शब्द तभी इस्तेमाल करो जब स्रोत में ऐसा हो।
5. सीधे उद्धरण केवल लेख में मौजूद उन्हीं शब्दों से बनाओ। शब्दशः बयान उपलब्ध न हो तो quote मत गढ़ो।
6. लेख के टेक्स्ट में हेडलाइन से अलग/विरोधी तथ्य हों तो skip करो।
7. अगर पक्के तथ्य कम हैं, तो छोटी और सावधान हेडलाइन लिखो; खाली जगह अनुमान से मत भरो।
8. पोस्टर/कैप्शन को स्रोत से शब्दशः कॉपी मत करो; अर्थ और तथ्य सुरक्षित रखते हुए संक्षेप में अपने शब्दों में लिखो।

पोस्टर में दो हिस्से हैं: बड़ा headline और नीचे quote_line।

दो layout में से चुनो:
- layout "A": सामान्य खबर, स्थानीय अपडेट या बयान/पलटवार वाली खबर।
  headline: 40 अक्षर तक, स्पष्ट और आकर्षक। खबर के तथ्य से बाहर न जाए।
  quote_line: 75 अक्षर तक। यदि लेख में स्पष्ट वास्तविक बयान है तो "बोले- '...'" / "कहा- '...'" / महिला के लिए "बोलीं- '...'" लिख सकते हो। बयान न हो तो सबसे अहम तथ्य की एक छोटी लाइन लिखो। कोई नकली quote नहीं।
- layout "B": तभी चुनो जब लेख में स्पष्ट, शब्दशः और महत्वपूर्ण सीधा बयान हो।
  headline: बयान का सटीक अंश, अधिकतम 65 अक्षर, उद्धरण चिह्नों के बिना।
  quote_line: किसने किस विषय पर कहा, अधिकतम 45 अक्षर; कोई नया तथ्य नहीं।
- layout B के लिए वास्तविक उद्धरण उपलब्ध न हो तो layout A चुनो।

caption:
- देवनागरी में 3-4 छोटी पंक्तियाँ।
- तथ्यात्मक, निष्पक्ष, और केवल स्रोत से समर्थित जानकारी।
- अंत में पाठकों से पूछो: "आपकी क्या राय है? कमेंट में बताएं।"
- पाठक को गुमराह करने वाला clickbait नहीं।

hashtags:
- 4 से 6 टैग।
- पहला हमेशा #Bharatdecode।
- खबर, जगह/जिला और विषय से जुड़े टैग ही चुनो। असंबंधित ट्रेंडिंग टैग नहीं।

सिर्फ यह JSON लौटाओ:
{{"skip": false, "skip_reason": "", "headline": "", "layout": "A", "quote_line": "", "caption": "", "hashtags": ["#Bharatdecode"]}}

खबर का स्रोत: {source}
क्षेत्र: {region}
शीर्षक: {title}
सारांश: {summary}
पूरा टेक्स्ट: {body}
"""

_state = {"cands": None, "dead": set()}
BASE = "https://generativelanguage.googleapis.com/v1beta"
SKIP_WORDS = (
    "image", "tts", "live", "audio", "thinking", "embedding",
    "exp", "robotics", "computer", "vision",
)


def _discover(key):
    r = requests.get(
        f"{BASE}/models",
        params={"key": key, "pageSize": 200},
        timeout=30,
    )
    r.raise_for_status()
    names = []
    for m in r.json().get("models", []):
        n = m["name"].split("/")[-1]
        if (
            "generateContent" in m.get("supportedGenerationMethods", [])
            and "flash" in n
            and not any(x in n for x in SKIP_WORDS)
        ):
            names.append(n)
    stable = sorted([n for n in names if "preview" not in n], reverse=True)
    prev = sorted([n for n in names if "preview" in n], reverse=True)
    return stable + prev


def _candidates(key):
    order = [GEMINI_MODEL, "gemini-flash-lite-latest"]
    try:
        found = _discover(key)
        print("  available flash models:", ", ".join(found[:8]) or "koi nahi")
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
    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    last = "koi model try nahi hua"
    for model in list(_state["cands"]):
        if model in _state["dead"]:
            continue
        for attempt in range(2):
            try:
                r = requests.post(
                    f"{BASE}/models/{model}:generateContent?key={key}",
                    json=request_body,
                    timeout=45,
                )
            except requests.RequestException as ex:
                last = f"{model}: {type(ex).__name__}"
                print(f"  {last}")
                break
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
            candidates = data.get("candidates") or []
            if (
                not candidates
                or "content" not in candidates[0]
                or not candidates[0]["content"].get("parts")
            ):
                return {"skip": True, "skip_reason": "Gemini ne content block kiya"}
            if _state["cands"][0] != model:
                _state["cands"].remove(model)
                _state["cands"].insert(0, model)
                print(f"  ab '{model}' use ho raha hai")
            txt = candidates[0]["content"]["parts"][0]["text"]
            txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
            return json.loads(txt)
    raise RuntimeError(f"Gemini sab models par fail. Last: {last}")


def make_draft(item, body):
    """Draft dict return karta hai, ya None agar skip karna hai."""
    prompt = PROMPT.format(
        source=item["source"],
        region=item["region"],
        title=item["title"],
        summary=item["summary"][:900],
        body=body[:3200],
    )
    d = _call(prompt)
    if d.get("skip"):
        print(f"  Gemini skip: {d.get('skip_reason')}")
        return None

    for key in ("headline", "quote_line", "caption"):
        if not str(d.get(key, "")).strip():
            print(f"  Gemini output mein '{key}' khali")
            return None

    d["layout"] = "B" if str(d.get("layout", "A")).strip().upper() == "B" else "A"
    d["headline"] = str(d["headline"]).strip().strip("\"'‘’“”")
    d["quote_line"] = str(d["quote_line"]).strip().lstrip("-–— ").strip()

    # Conservative output check against blocked content.
    out_text = " ".join([d["headline"], d["quote_line"], d["caption"]])
    hit = blocked_reason(out_text)
    if hit:
        print(f"  output mein blocked shabd: {hit}")
        return None

    tags = ["#Bharatdecode"]
    for tag in d.get("hashtags", []):
        tag = "#" + str(tag).strip().lstrip("#").replace(" ", "")
        if len(tag) > 1 and tag.lower() not in [x.lower() for x in tags]:
            tags.append(tag)
    d["hashtags"] = tags[:6]
    d["full_caption"] = (
        f"{d['caption'].strip()}\n\n{' '.join(d['hashtags'])}"
        f"\n\nस्रोत: {item['source']}\n{item['link']}"
    )
    return d
