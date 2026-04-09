import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import crud
from app.keyboards.inline import watch_button


logger = logging.getLogger(__name__)
router = Router()
settings = get_settings()


class MovieUploadState(StatesGroup):
    waiting_video = State()
    waiting_more_videos = State()
    waiting_title = State()
    waiting_description = State()
    waiting_preview = State()


async def _start_upload(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MovieUploadState.waiting_video)
    text = (
        "Kino yuklash boshlandi.\n"
        "Iltimos, kinoni boshqa chatdan botga forward qiling yoki videoni yuboring."
    )
    if isinstance(event, CallbackQuery):
        await event.message.answer(text)
        await event.answer()
    else:
        await event.answer(text)


@router.message(Command("addmovie"))
async def add_movie_cmd(message: Message, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        await message.answer("Bu buyruq faqat adminlar uchun.")
        return
    await _start_upload(message, state)


@router.callback_query(F.data == "admin:add")
async def add_movie_callback(call: CallbackQuery, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        await call.answer("Ruxsat yo'q", show_alert=True)
        return
    await _start_upload(call, state)


@router.message(MovieUploadState.waiting_video, F.video)
async def upload_video_step(message: Message, state: FSMContext) -> None:
    await state.update_data(file_ids=[message.video.file_id])
    await state.set_state(MovieUploadState.waiting_more_videos)
    await message.answer(
        "1-qism saqlandi.\n"
        "Agar yana qism bo'lsa video yuboring.\n"
        "Hammasi bo'lsa /done yuboring."
    )


@router.message(MovieUploadState.waiting_video)
async def upload_video_invalid(message: Message) -> None:
    await message.answer("Iltimos, video yuboring yoki forward qiling.")


@router.message(MovieUploadState.waiting_more_videos, F.video)
async def upload_more_video_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    file_ids = list(data.get("file_ids", []))
    file_ids.append(message.video.file_id)
    await state.update_data(file_ids=file_ids)
    await message.answer(
        f"{len(file_ids)}-qism saqlandi. Yana yuboring yoki /done deb yakunlang."
    )


@router.message(MovieUploadState.waiting_more_videos, Command("done"))
async def upload_videos_done(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    file_ids = list(data.get("file_ids", []))
    if not file_ids:
        await message.answer("Avval kamida 1 ta video yuboring.")
        return
    await state.set_state(MovieUploadState.waiting_title)
    await message.answer("Kino nomini yuboring:")


@router.message(MovieUploadState.waiting_more_videos)
async def upload_more_video_invalid(message: Message) -> None:
    await message.answer("Video yuboring yoki /done deb yakunlang.")


@router.message(MovieUploadState.waiting_title, F.text)
async def upload_title_step(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if not title:
        await message.answer("Nom bo'sh bo'lmasligi kerak.")
        return
    await state.update_data(title=title)
    await state.set_state(MovieUploadState.waiting_description)
    await message.answer("Tavsifni yuboring yoki /skip deb yuboring.")


@router.message(MovieUploadState.waiting_description, Command("skip"))
async def skip_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=None)
    await state.set_state(MovieUploadState.waiting_preview)
    await message.answer("Preview rasm yuboring yoki /skip deb o'tkazib yuboring.")


@router.message(MovieUploadState.waiting_description, F.text)
async def upload_description_step(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip() or None)
    await state.set_state(MovieUploadState.waiting_preview)
    await message.answer("Preview rasm yuboring yoki /skip deb o'tkazib yuboring.")


@router.message(MovieUploadState.waiting_preview, Command("skip"))
async def skip_preview(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await _finalize_movie(message, state, session, preview_file_id=None)


@router.message(MovieUploadState.waiting_preview, F.photo)
async def upload_preview_step(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    preview_file_id = message.photo[-1].file_id
    await _finalize_movie(message, state, session, preview_file_id=preview_file_id)


@router.message(MovieUploadState.waiting_preview)
async def upload_preview_invalid(message: Message) -> None:
    await message.answer("Preview uchun rasm yuboring yoki /skip deb yuboring.")


async def _finalize_movie(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    preview_file_id: str | None,
) -> None:
    data = await state.get_data()
    title = data["title"]
    description = data.get("description")
    file_ids = list(data.get("file_ids", []))
    if not file_ids:
        await message.answer("Video topilmadi. Qaytadan /addmovie bilan boshlang.")
        await state.clear()
        return
    file_id = file_ids[0]
    next_number = await crud.get_next_movie_number(session)
    deep_link = f"https://t.me/{settings.bot_username}?start=watch_{next_number}"
    text = f"🎬 #{next_number} - {title}"
    if description:
        text += f"\n\n📝 {description}"

    try:
        if preview_file_id:
            sent = await message.bot.send_photo(
                settings.channel_id,
                photo=preview_file_id,
                caption=text,
                reply_markup=watch_button(deep_link),
            )
        else:
            sent = await message.bot.send_message(
                settings.channel_id,
                text=text,
                reply_markup=watch_button(deep_link),
            )
    except Exception:
        logger.exception("Kanalga post yuborishda xatolik bo'ldi")
        await message.answer(
            "❌ Kanalga e'lon yuborilmadi. Kanal ID va bot huquqlarini tekshiring."
        )
        return

    try:
        movie = await crud.create_movie(
            session,
            title=title,
            description=description,
            file_id=file_id,
            preview_file_id=preview_file_id,
            channel_message_id=sent.message_id,
            channel_chat_id=sent.chat.id,
            added_by=message.from_user.id,
        )
    except Exception:
        await session.rollback()
        logger.exception("Kino bazaga saqlanmadi (post id=%s)", sent.message_id)
        await message.answer(
            "❌ Kino bazaga saqlanmadi. Iltimos, qayta urinib ko'ring."
        )
        return

    # Movie already saved. Parts save should not break the whole flow.
    try:
        await crud.add_movie_parts(session, movie.id, file_ids)
    except Exception:
        await session.rollback()
        logger.exception("Kino qismlari saqlanmadi, fallback bitta file_id orqali ishlaydi.")
        await message.answer(
            "⚠️ Kino saqlandi, lekin qismlar bazaga to'liq yozilmadi. "
            "Hozircha birinchi video orqali ishlaydi."
        )

    post_link = f"https://t.me/c/{str(settings.channel_id).replace('-100', '')}/{sent.message_id}"
    await message.answer(
        "✅ Kino muvaffaqiyatli qo'shildi.\n"
        f"Raqami: #{movie.movie_number}\n"
        f"Kanal posti: {post_link}"
    )
    logger.info("Kino qo'shildi: #%s - %s", movie.movie_number, movie.title)
    await state.clear()
