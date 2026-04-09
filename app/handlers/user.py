from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import crud
from app.keyboards.inline import (
    force_sub_check_keyboard,
    movies_page_keyboard,
    user_main_inline,
    watch_button,
)
from app.utils.helpers import format_movie_details

router = Router()
settings = get_settings()


class UserSearchState(StatesGroup):
    waiting_movie_number = State()


def _deep_link(movie_number: int) -> str:
    return f"https://t.me/{settings.bot_username}?start=watch_{movie_number}"


async def _send_movie_details(message: Message, session: AsyncSession, movie_number: int) -> None:
    movie = await crud.get_movie_by_number(session, movie_number)
    if not movie:
        await message.answer("Bunday raqamdagi kino topilmadi.")
        return
    await message.answer(
        format_movie_details(movie.movie_number, movie.title, movie.description, movie.views_count, movie.added_at),
        reply_markup=watch_button(_deep_link(movie.movie_number)),
    )


async def _send_movie_parts(message: Message, session: AsyncSession, movie_number: int) -> bool:
    movie = await crud.get_movie_by_number(session, movie_number)
    if not movie:
        await message.answer("Kechirasiz, bu kino mavjud emas.")
        return False
    parts = await crud.get_movie_parts(session, movie.id)
    if not parts:
        await message.answer_video(video=movie.file_id, caption=f"🎬 #{movie.movie_number} - {movie.title}")
        return True

    total = len(parts)
    for part in parts:
        caption = (
            f"🎬 #{movie.movie_number} - {movie.title}\n"
            f"📦 Qism: {part.part_number}/{total}"
        )
        await message.answer_video(video=part.file_id, caption=caption)
    return True


@router.message(CommandStart(deep_link=True))
async def start_with_deeplink(message: Message, command: CommandObject, session: AsyncSession) -> None:
    await crud.create_or_update_user(session, user_id=message.from_user.id, username=message.from_user.username, first_name=message.from_user.first_name or "Foydalanuvchi")
    arg = command.args or ""
    if arg.startswith("watch_") and arg.replace("watch_", "", 1).isdigit():
        n = int(arg.replace("watch_", "", 1))
        ok = await _send_movie_parts(message, session, n)
        if ok:
            await crud.increment_movie_views(session, n)
            return
    await message.answer("Noto'g'ri havola. /start buyrug'idan foydalaning.")


@router.message(CommandStart())
async def start_cmd(message: Message, session: AsyncSession) -> None:
    await crud.create_or_update_user(session, user_id=message.from_user.id, username=message.from_user.username, first_name=message.from_user.first_name or "Foydalanuvchi")
    await message.answer(
        "Assalomu alaykum! Kino kutubxonasiga xush kelibsiz.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Asosiy menyu:", reply_markup=user_main_inline())


@router.message(Command("movies"))
async def movies_cmd(message: Message, session: AsyncSession) -> None:
    movies = await crud.list_movies(session, page=1, per_page=10)
    if not movies:
        await message.answer("Hozircha kinolar mavjud emas.")
        return
    await message.answer("Kinolar ro'yxati:", reply_markup=movies_page_keyboard([(m.movie_number, m.title) for m in movies], 1, (await crud.count_movies(session)) > 10))


@router.callback_query(F.data.startswith("movies:"))
async def movies_callback(call: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    p = call.data.split(":")[1]
    if p == "number":
        await state.set_state(UserSearchState.waiting_movie_number)
        await call.message.answer("Kino raqamini yuboring (masalan: 42).")
        await call.answer()
        return
    if not p.isdigit():
        await call.answer("Xato sahifa.", show_alert=True)
        return
    page = int(p)
    movies = await crud.list_movies(session, page=page, per_page=10)
    if not movies:
        await call.answer("Bu sahifada kino yo'q.", show_alert=True)
        return
    await call.message.edit_text("Kinolar ro'yxati:", reply_markup=movies_page_keyboard([(m.movie_number, m.title) for m in movies], page, (await crud.count_movies(session)) > page * 10))
    await call.answer()


@router.callback_query(F.data.startswith("movie:"))
async def movie_callback(call: CallbackQuery, session: AsyncSession) -> None:
    value = call.data.split(":")[1]
    if value.isdigit():
        await _send_movie_details(call.message, session, int(value))
    await call.answer()


@router.message(Command("movie"))
async def movie_cmd(message: Message, command: CommandObject, session: AsyncSession) -> None:
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer("Iltimos, kino raqamini kiriting. Masalan: /movie 7")
        return
    await _send_movie_details(message, session, int(arg))


@router.message(UserSearchState.waiting_movie_number, F.text.regexp(r"^\d+$"))
async def number_state(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await _send_movie_details(message, session, int(message.text))
    await state.clear()


@router.message(F.text.regexp(r"^\d+$"))
async def number_as_movie(message: Message, session: AsyncSession) -> None:
    await _send_movie_details(message, session, int(message.text))


@router.message(Command("search"))
async def search_cmd(message: Message, command: CommandObject, session: AsyncSession) -> None:
    query = (command.args or "").strip()
    if not query:
        await message.answer("Qidiruv uchun matn kiriting. Masalan: /search avatar")
        return
    movies = await crud.search_movies_by_title(session, query)
    if not movies:
        await message.answer("Hech narsa topilmadi.")
    elif len(movies) == 1:
        await _send_movie_details(message, session, movies[0].movie_number)
    else:
        await message.answer("Topilgan kinolar:\n" + "\n".join(f"#{m.movie_number} - {m.title}" for m in movies[:20]))


@router.message(F.text == "🎬 Kinolar ro'yxati")
async def text_movies(message: Message, session: AsyncSession) -> None:
    await movies_cmd(message, session)


@router.message(F.text == "🔍 Qidirish")
async def text_search_help(message: Message) -> None:
    await message.answer("Qidiruv uchun: /search nomi")


@router.message(F.text == "ℹ️ Bot haqida")
@router.callback_query(F.data == "help:about")
async def about_handler(event: Message | CallbackQuery) -> None:
    text = "Bu bot kino kutubxonasi uchun yaratilgan."
    if isinstance(event, CallbackQuery):
        await event.message.answer(text)
        await event.answer()
    else:
        await event.answer(text)


@router.callback_query(F.data == "help:search")
async def search_help_callback(call: CallbackQuery) -> None:
    await call.message.answer("Qidiruv: /search nomi")
    await call.answer()


@router.callback_query(F.data == "sub:check")
async def sub_check_callback(call: CallbackQuery, session: AsyncSession) -> None:
    s = await crud.get_or_create_bot_settings(session)
    if not s.force_sub_enabled or not s.force_sub_channel_id:
        await call.message.answer("Majburiy a'zolik hozir o'chirilgan.")
        await call.answer()
        return
    try:
        member = await call.bot.get_chat_member(s.force_sub_channel_id, call.from_user.id)
    except Exception:
        await call.message.answer("A'zolikni tekshirib bo'lmadi. Keyinroq qayta urinib ko'ring.")
        await call.answer()
        return

    if member.status in {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    }:
        await call.message.answer("✅ Ajoyib! Siz kanalga a'zo ekansiz. Endi botdan foydalanishingiz mumkin.")
    else:
        await call.message.answer(
            "❌ Hali kanalga a'zo emassiz.",
            reply_markup=force_sub_check_keyboard(s.force_sub_channel_link),
        )
    await call.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def fallback_text(message: Message) -> None:
    await message.answer("Buyruq tushunarsiz. /start yoki /movies dan foydalaning.")
