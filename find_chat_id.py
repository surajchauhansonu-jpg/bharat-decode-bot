"""Bot jin chats/groups mein hai unki ID dhundo, aur har group mein ID likh ke bhejo.
Pehle bot ko group mein add karo aur group mein koi message bhejo (jaise /start@BotUsername)."""
import os

import requests

tok = os.environ["TELEGRAM_BOT_TOKEN"]
base = f"https://api.telegram.org/bot{tok}"

r = requests.get(f"{base}/getUpdates", params={"timeout": 0}, timeout=30).json()
if not r.get("ok"):
    print("getUpdates fail:", r.get("description"))
    raise SystemExit(1)

chats = {}
for u in r["result"]:
    for key in ("message", "edited_message", "channel_post", "my_chat_member"):
        ch = (u.get(key) or {}).get("chat")
        if ch:
            chats[ch["id"]] = ch
    cb = (u.get("callback_query") or {}).get("message") or {}
    if cb.get("chat"):
        chats[cb["chat"]["id"]] = cb["chat"]

if not chats:
    print("Koi chat nahi mili. Bot ko group mein add karo, group mein ek message bhejo "
          "(jaise /start@BotUsername), phir ye workflow dobara chalao.")
    raise SystemExit(0)

for cid, ch in chats.items():
    name = ch.get("title") or ch.get("username") or ch.get("first_name") or ""
    print(f"CHAT  id={cid}  type={ch.get('type')}  name={name}")
    if ch.get("type") in ("group", "supergroup", "channel"):
        resp = requests.post(f"{base}/sendMessage", timeout=30, data={
            "chat_id": cid,
            "text": f"✅ Is group ki ID: {cid}\nYehi GitHub secret MANUAL_CHAT_ID mein daalni hai."}).json()
        print("   group mein ID bhej di" if resp.get("ok") else f"   bhej nahi paya: {resp.get('description')}")
