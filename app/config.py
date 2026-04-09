import os
from dataclasses import dataclass
from typing import Set

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> Set[int]:
    result: Set[int] = set()
    for chunk in raw.split(','):
        chunk = chunk.strip()
        if chunk.isdigit():
            result.add(int(chunk))
    return result


@dataclass(slots=True)
class Settings:
    bot_token: str
    admin_ids: Set[int]
    channel_id: int
    bot_username: str
    database_url: str


def get_settings() -> Settings:
    database_url = os.getenv('DATABASE_URL', '').strip() or 'sqlite+aiosqlite:///movies.db'
    bot_token = os.getenv('BOT_TOKEN', '').strip()
    if not bot_token:
        raise ValueError('BOT_TOKEN .env da bo\'lishi shart.')
    channel_raw = os.getenv('CHANNEL_ID', '').strip()
    if not channel_raw:
        raise ValueError('CHANNEL_ID .env da bo\'lishi shart.')

    return Settings(
        bot_token=bot_token,
        admin_ids=_parse_admin_ids(os.getenv('ADMIN_IDS', '')),
        channel_id=int(channel_raw),
        bot_username=os.getenv('BOT_USERNAME', '').strip().lstrip('@'),
        database_url=database_url,
    )
