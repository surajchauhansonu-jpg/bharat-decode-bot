import json
import time

import requests


class Telegram:
    def __init__(self, token, chat_id):
        self.base = f"https://api.telegram.org/bot{token}"
        self.chat_id = int(chat_id)

    def _call(self, method, **kw):
        files = kw.pop("files", None)
        r = requests.post(f"{self.base}/{method}", data=kw, files=files, timeout=70)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method}: {data}")
        return data["result"]

    def send_message(self, text):
        return self._call("sendMessage", chat_id=self.chat_id, text=text[:4000],
                          disable_web_page_preview="true")

    def send_photo_with_buttons(self, jpg, draft_id, tag="1"):
        kb = {"inline_keyboard": [[
            {"text": f"✅ Design {tag} post karo", "callback_data": f"ok:{draft_id}:{tag}"},
            {"text": "❌ Reject", "callback_data": f"no:{draft_id}:{tag}"},
        ]]}
        return self._call("sendPhoto", chat_id=self.chat_id,
                          reply_markup=json.dumps(kb),
                          files={"photo": ("poster.jpg", jpg, "image/jpeg")})

    def drain(self):
        """Purane pending updates saaf karo, taaki purane button dab na jayein."""
        ups = self._call("getUpdates", timeout=0)
        return (ups[-1]["update_id"] + 1) if ups else None

    def get_updates(self, offset, timeout):
        kw = {"timeout": timeout, "allowed_updates": json.dumps(["callback_query"])}
        if offset is not None:
            kw["offset"] = offset
        return self._call("getUpdates", **kw)

    def answer_callback(self, cb_id, text=""):
        try:
            self._call("answerCallbackQuery", callback_query_id=cb_id, text=text)
        except Exception:
            pass

    def set_status(self, message_id, text):
        """Buttons hata ke photo ke neeche status likh do."""
        try:
            self._call("editMessageCaption", chat_id=self.chat_id,
                       message_id=message_id, caption=text)
        except Exception as ex:
            print("status edit fail:", ex)


def wait_for_decision(tg, draft_id, message_id, minutes, offset):
    """("ok"/"no", design_tag) ya (None, None) timeout par."""
    deadline = time.time() + minutes * 60
    while True:
        remaining = deadline - time.time()
        if remaining <= 2:
            return None, None
        for u in tg.get_updates(offset, timeout=int(min(50, remaining))):
            offset = u["update_id"] + 1
            cb = u.get("callback_query")
            if not cb:
                continue
            msg = cb.get("message") or {}
            if msg.get("chat", {}).get("id") != tg.chat_id:
                continue
            parts = (cb.get("data") or "").split(":")
            action = parts[0]
            did = parts[1] if len(parts) > 1 else ""
            tag = parts[2] if len(parts) > 2 else "1"
            if did != draft_id:
                tg.answer_callback(cb["id"], "Ye purana draft hai")
                continue
            tg.answer_callback(cb["id"], "Ok")
            return action, tag
