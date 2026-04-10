from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import crud
from app.keyboards.inline import watch_button
from app.utils.helpers import short_description


router = Router()
settings = get_settings()


def _deep_link(number: int) -> str:
    return f"https://t.me/{settings.bot_username}?start=watch_{number}"


@router.inline_query()
async def inline_handler(query: InlineQuery, session: AsyncSession) -> None:
    raw = query.query.strip()
    if not raw:
        movies = await crud.list_movies_desc(session, 30)
    elif raw.isdigit():
        movie = await crud.get_movie_by_number(session, int(raw))
        movies = [movie] if movie else []
    else:
        movies = await crud.search_movies_by_title(session, raw, limit=30)

    results = []
    for movie in movies:
        if not movie:
            continue
        number = movie.movie_number
        title = f"#{number} - {movie.title}"
        desc = short_description(movie.description, 50)
        content = InputTextMessageContent(
            message_text=f"🎬 {title}\n📝 {desc}\n\nKo'rish uchun tugmani bosing."
        )
        results.append(
            InlineQueryResultArticle(
                id=str(number),
                title=title,
                description=desc,
                input_message_content=content,
                reply_markup=watch_button(_deep_link(number)),
            )
        )
    await query.answer(results, cache_time=5, is_personal=True)
