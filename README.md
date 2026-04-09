# Uzbek Movie Library Bot (aiogram 3.x)

Telegram bot for movie library management with full Uzbek interface.

## Main capabilities

- Aiogram 3.x async architecture.
- PostgreSQL for production (`asyncpg`) and SQLite fallback for local (`aiosqlite`).
- Admin-only movie upload flow (FSM).
- Multi-part movie support:
  - one movie can contain multiple video parts
  - users receive parts sequentially when they press **Ko'rish**
- Channel announcement post:
  - only one post per movie
  - actual movie video is sent in private chat, not in channel post
- Deep link watch:
  - `https://t.me/BOT_USERNAME?start=watch_<number>`
- Admin panel:
  - add/edit/delete movie
  - replace all parts in one action
  - stats, users list, broadcast
  - forced subscription management (on/off + channel id/link)
- Forced subscription middleware:
  - when enabled, users must join channel before using bot
  - includes `Tekshirish` button
- Inline mode:
  - `@botusername <query>`
  - empty query => latest movies
  - number => exact movie
  - text => title search

## Project structure

```text
bot.py
app/
  config.py
  db/
    database.py
    models.py
    crud.py
  handlers/
    user.py
    admin.py
    movie_upload.py
    inline.py
  keyboards/
    inline.py
  middlewares/
    auth.py
    subscription.py
  utils/
    helpers.py
```

## Environment variables

Create `.env` from `.env.example`:

```env
BOT_TOKEN=your_token
ADMIN_IDS=123456789,987654321
CHANNEL_ID=-1001234567890
BOT_USERNAME=YourBotUsername
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

If `DATABASE_URL` is empty, bot uses local SQLite:

`sqlite+aiosqlite:///movies.db`

## Local run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set `.env`.
3. Start bot:
   ```bash
   python bot.py
   ```

## Railway deploy

1. Push repository to GitHub.
2. Connect repository in Railway.
3. Add environment variables in Railway.
4. Deploy (Railway uses `Procfile` -> `python bot.py`).

## Important notes

- Use `postgresql+asyncpg://` in production DB URL.
- Do not install/use `psycopg2`.
- On startup, bot auto-creates missing tables and missing columns.
- All user/admin messages and buttons are Uzbek.
- See `RAILWAY_CHECKLIST.md` for production checklist.
