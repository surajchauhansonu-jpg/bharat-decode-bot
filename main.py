import json
import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import ai
import facebook
import filters
import news
import poster
from config import (ACTIVE_FROM_HOUR, ACTIVE_TO_HOUR, MAX_GEMINI_CHECKS,
                    WAIT_MINUTES)
from telegram_bot import Telegram, wait_for_decision

SEEN_FILE = "seen.json"


def load_seen():
    try:
        return json.load(open(SEEN_FILE))
    except Exception:
        return []


def save_seen(seen):
    json.dump(seen[-1500:], open(SEEN_FILE, "w"), ensure_ascii=False, indent=0)


def pick_draft(seen):
    """Pehla article jo saare filter + Gemini pass kare. (item, draft, photo) return."""
    items = [i for i in news.collect() if i["link"] not in seen]
    print(f"{len(items)} nayi news mili")
    items.sort(key=filters.score, reverse=True)
    checks = 0
    for it in items:
        if checks >= MAX_GEMINI_CHECKS or filters.score(it) < 3:
            break
        print(f"\n[{filters.score(it)}] {it['source']}: {it['title']}")
        hit = filters.blocked_reason(it["title"] + " " + it["summary"])
        if hit:
            print(f"  blocked ({hit})")
            seen.append(it["link"])
            continue
        try:
            body, og = news.fetch_article(it["link"])
        except Exception as ex:
            print("  article fetch fail:", ex)
            continue
        hit = filters.blocked_reason(body)
        if hit:
            print(f"  blocked in body ({hit})")
            seen.append(it["link"])
            continue
        photo = None
        for url in (og, it["image"]):
            if url:
                try:
                    photo = news.download_image(url)
                    break
                except Exception as ex:
                    print("  image fail:", ex)
        if photo is None:
            print("  photo nahi mili, skip")
            seen.append(it["link"])
            continue
        checks += 1
        seen.append(it["link"])
        try:
            draft = ai.make_draft(it, body)
        except Exception as ex:
            print("  Gemini fail:", ex)
            continue
        if draft:
            return it, draft, photo
    return None, None, None


def main():
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    if os.getenv("FORCE") != "1" and not (ACTIVE_FROM_HOUR <= now.hour < ACTIVE_TO_HOUR):
        print("Active time ke bahar, exit")
        return

    seen = load_seen()
    try:
        item, draft, photo = pick_draft(seen)
    finally:
        save_seen(seen)
    if not item:
        print("Is baar post layak news nahi mili")
        return

    jpg = poster.make_poster(photo, draft["headline"], draft["quote_line"])

    tg = Telegram(os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"])
    offset = tg.drain()
    draft_id = uuid.uuid4().hex[:8]
    tg.send_message(f"📝 CAPTION\n\n{draft['full_caption']}\n\n"
                    f"🔗 {item['title']}\n{item['link']}")
    msg = tg.send_photo_with_buttons(jpg, draft_id)
    print(f"Telegram par draft bheja, {WAIT_MINUTES} min wait...")

    decision = wait_for_decision(tg, draft_id, msg["message_id"], WAIT_MINUTES, offset)
    if decision == "ok":
        try:
            facebook.post_photo(os.environ["FB_PAGE_ID"], os.environ["FB_PAGE_TOKEN"],
                                jpg, draft["full_caption"])
            tg.set_status(msg["message_id"], "✅ Facebook par post ho gaya")
            print("Posted")
        except Exception as ex:
            tg.set_status(msg["message_id"], "⚠️ Post fail hua")
            tg.send_message(f"Facebook post fail:\n{ex}")
            raise
    elif decision == "no":
        tg.set_status(msg["message_id"], "❌ Reject kiya")
    else:
        tg.set_status(msg["message_id"], "⌛ Time khatam, draft expire")


if __name__ == "__main__":
    main()
