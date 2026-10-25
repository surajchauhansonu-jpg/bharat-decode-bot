# Bharat Decode Bot

Bihar / India / World ki news me se **leader ke bayan wali** khabar, aur **cricket ki badi khabar** chunta hai, poster banata hai,
Telegram par approve ke liye bhejta hai, approve hone par Facebook page par post karta hai.
Rape / sexual-violence se judi koi bhi news skip hoti hai (3 jagah filter: title+summary, article body, Gemini output).

## Setup (ek baar)
1. GitHub par naya repo banao (e.g. `bharat-decode-bot`) aur ye saari files upload karo.
2. **Naya Telegram bot** banao @BotFather se (Cine Chaska wala token dobara mat use karna, warna dono bot ek-dusre ke button updates kha jayenge).
   Apna chat ID @userinfobot se lo.
3. Repo > Settings > Secrets and variables > Actions me ye 5 secrets daalo:
   `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `FB_PAGE_ID`, `FB_PAGE_TOKEN`
4. Actions tab > "Bharat Decode Bot" > Run workflow (force = 1) se test karo.

## Kaise chalta hai
- Har 30 min (6am-11pm IST) ek run: news uthata hai -> best candidate -> Gemini draft -> poster -> Telegram.
- Telegram par pehle caption + link aata hai, phir poster with ✅ / ❌ buttons.
- 25 min tak koi button nahi dabaya to draft expire ho jata hai (agle run me nayi news aayegi).

## Files
- `config.py` : feeds, timing, limits
- `filters.py` : rape-filter, leaders list, bayan keywords, scoring
- `news.py` : RSS + article fetch
- `ai.py` : Gemini prompt (headline, quote line, caption, hashtags)
- `poster.py` : 1080x1350 poster (aapka design)
- `check_feeds.py` : `python check_feeds.py` se dekho kaun si feed chal rahi hai
- `test_poster.py` : `python test_poster.py photo.jpg` se poster preview

## Note
- Feed URLs sandbox se verify nahi ho paaye. Pehle `check_feeds.py` chalao, jo FAIL ho use config.py me badal do.
- Local test ke liye `libraqm` chahiye (Hindi shaping): Ubuntu me `sudo apt install libraqm0 libfribidi0`.
