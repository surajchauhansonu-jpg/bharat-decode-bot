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

    def send_photo_with_buttons(self, jpg, draft_id):
        kb = {"inline_keyboard": [[
            {"text": "✅ Post karo", "callback_data": f"ok:{draft_id}"},
            {"text": "❌ Reject", "callback_data": f"no:{draft_id}"},
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
    """'ok' / 'no' / None (timeout) return karta hai."""
    deadline = time.time() + minutes * 60
    while True:
        remaining = deadline - time.time()
        if remaining <= 2:
            return None
        for u in tg.get_updates(offset, timeout=int(min(50, remaining))):
            offset = u["update_id"] + 1
            cb = u.get("callback_query")
            if not cb:
                continue
            msg = cb.get("message") or {}
            if msg.get("chat", {}).get("id") != tg.chat_id:
                continue
            action, _, did = (cb.get("data") or "").partition(":")
            if did != draft_id:
                tg.answer_callback(cb["id"], "Ye purana draft hai")
                continue
            tg.answer_callback(cb["id"], "Ok")
            return action
