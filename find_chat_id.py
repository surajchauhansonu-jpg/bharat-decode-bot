"""Bot jin groups mein hai unki ID dhundo, aur group mein ID likh ke bhejo.

Steps: 1) Bot ko group mein add karo  2) Ye workflow chalao
       3) 3 minute ke andar group mein  /start@BotUsername  bhejo."""
import json
import os
import time

import requests

tok = os.environ["TELEGRAM_BOT_TOKEN"]
base = f"https://api.telegram.org/bot{tok}"
WAIT = int(os.getenv("WAIT_SECONDS", "200"))
# Telegram pichli allowed_updates yaad rakhta hai (approve flow sirf callback_query maangta tha),
# isliye yahan saaf-saaf message wale updates maange.
ALLOWED = json.dumps(["message", "edited_message", "channel_post", "my_chat_member", "callback_query"])

wh = requests.get(f"{base}/getWebhookInfo", timeout=30).json().get("result", {})
if wh.get("url"):
    print("Webhook laga hai, getUpdates kaam nahi karega:", wh["url"])

print(f"Ab {WAIT} second tak sun raha hu. Group mein /start@BotUsername bhejo.")
deadline = time.time() + WAIT
offset, seen, answered = None, {}, set()
while time.time() < deadline:
    params = {"timeout": 20, "allowed_updates": ALLOWED}
    if offset is not None:
        params["offset"] = offset
    r = requests.get(f"{base}/getUpdates", params=params, timeout=45).json()
    if not r.get("ok"):
        print("getUpdates fail:", r.get("description"))
        break
    for u in r["result"]:
        offset = u["update_id"] + 1
        chat = None
        for key in ("message", "edited_message", "channel_post", "my_chat_member"):
            chat = chat or (u.get(key) or {}).get("chat")
        chat = chat or ((u.get("callback_query") or {}).get("message") or {}).get("chat")
        if not chat:
            continue
        cid = chat["id"]
        if cid not in seen:
            seen[cid] = chat
            name = chat.get("title") or chat.get("username") or chat.get("first_name") or ""
            print(f"CHAT  id={cid}  type={chat.get('type')}  name={name}")
        if chat.get("type") in ("group", "supergroup", "channel") and cid not in answered:
            resp = requests.post(f"{base}/sendMessage", timeout=30, data={
                "chat_id": cid,
                "text": f"✅ Is group ki ID: {cid}\nYehi GitHub secret MANUAL_CHAT_ID mein daalni hai."}).json()
            answered.add(cid)
            print("   group mein ID bhej di" if resp.get("ok") else f"   bhej nahi paya: {resp.get('description')}")
    if answered:
        break

if not seen:
    print("Koi message nahi aaya. Check karo: (1) bot group ka member hai, "
          "(2) workflow chalne ke baad group mein /start@BotUsername bheja.")
