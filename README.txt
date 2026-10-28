# Bharat Decode Bot updates

Replace these three files in your repository:
- `config.py`
- `news.py`
- `ai.py`

Keep your existing `main.py`, `bot.yml`, `filters.py`, `poster.py`, `facebook.py`, and Telegram files unchanged.

Important notes:
- RSS collection remains the primary route where a feed is configured.
- The five requested site pages are best-effort fallbacks.
- Page scraping accepts a result only when it can detect a publication date within `MAX_AGE_HOURS`. Some sites may render content using JavaScript or different markup, so check GitHub Actions logs for `[site scrape fail]` and item counts.
- The scraper does not bypass logins, paywalls, or access controls.
- A source page may not expose an article image or date in the markup; such items can be skipped rather than guessed.
- This is a first integration pass, not a guarantee that every site will return results on every run.
