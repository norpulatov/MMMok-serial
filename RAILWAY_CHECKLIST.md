# Railway Production Checklist

Use this checklist before going live.

## 1) Environment

- [ ] `BOT_TOKEN` is set.
- [ ] `ADMIN_IDS` is set (your Telegram numeric ID included).
- [ ] `CHANNEL_ID` is set correctly (`-100...` format).
- [ ] `BOT_USERNAME` is set without `@`.
- [ ] `DATABASE_URL` uses `postgresql+asyncpg://...`.

## 2) Bot permissions

- [ ] Bot is added to your channel.
- [ ] Bot has permission to post messages in channel.
- [ ] If forced subscription is enabled, bot can read member status.

## 3) Build/runtime

- [ ] `requirements.txt` includes `aiogram`, `SQLAlchemy`, `asyncpg`, `aiosqlite`.
- [ ] `Procfile` has `worker: python bot.py`.
- [ ] Python version is pinned via Railway/Nixpacks config.

## 4) Functional checks

- [ ] `/start` works and shows inline main menu.
- [ ] `/admin` works for admin IDs.
- [ ] Add movie flow works:
  - [ ] send one or more video parts
  - [ ] finish with `/done`
  - [ ] title/description/preview step
  - [ ] single channel announcement post is created
- [ ] Deep link watch (`start=watch_<number>`) sends video/parts.
- [ ] Movie list/search/detail commands work.
- [ ] Inline mode works (`@botusername query`).
- [ ] Forced subscription on/off works from admin panel.

## 5) Data integrity

- [ ] Deleting a movie re-numbers `movie_number` without gaps.
- [ ] Editing movie parts replaces old parts only for selected movie.
- [ ] Other movies remain unchanged after edit/delete actions.

## 6) Monitoring

- [ ] Railway logs show bot started successfully.
- [ ] No repeating exceptions in logs during normal usage.
- [ ] Test broadcast with small user set first.
