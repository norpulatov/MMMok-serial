from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def watch_button(deep_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="▶️ Ko'rish", url=deep_link)]]
    )


def user_main_inline() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Kinolar ro'yxati", callback_data="movies:1")
    builder.button(text="🔍 Qidirish", callback_data="help:search")
    builder.button(text="ℹ️ Bot haqida", callback_data="help:about")
    builder.adjust(1)
    return builder.as_markup()


def movies_page_keyboard(movies: list[tuple[int, str]], page: int, has_next: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for number, title in movies:
        builder.button(text=f"#{number} - {title}", callback_data=f"movie:{number}")

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"movies:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text="🔢 Raqam bilan", callback_data="movies:number"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"movies:{page + 1}"))

    builder.adjust(1)
    markup = builder.as_markup()
    markup.inline_keyboard.append(nav_row)
    return markup


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Kino qo'shish", callback_data="admin:add")
    builder.button(text="📋 Kinolar ro'yxati", callback_data="admin:list:1")
    builder.button(text="📊 Statistika", callback_data="admin:stats")
    builder.button(text="👥 Foydalanuvchilar", callback_data="admin:users")
    builder.button(text="📢 Xabar yuborish", callback_data="admin:broadcast")
    builder.button(text="📡 Majburiy a'zolik", callback_data="admin:forcesub")
    builder.adjust(1)
    return builder.as_markup()


def admin_movie_actions(movie_number: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Tahrirlash", callback_data=f"admin:edit:{movie_number}"
                ),
                InlineKeyboardButton(
                    text="🗑 O'chirish", callback_data=f"admin:delete:{movie_number}"
                ),
            ]
        ]
    )


def admin_movies_page_keyboard(
    movies: list[tuple[int, str]], page: int, has_next: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for number, title in movies:
        builder.button(text=f"#{number} - {title}", callback_data=f"admin:movie:{number}")
    builder.adjust(1)

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"admin:list:{page - 1}"))
    if has_next:
        nav.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"admin:list:{page + 1}"))
    if nav:
        markup = builder.as_markup()
        markup.inline_keyboard.append(nav)
        return markup
    return builder.as_markup()


def admin_edit_fields_keyboard(movie_number: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Sarlavha", callback_data=f"admin:editfield:title:{movie_number}"
                ),
                InlineKeyboardButton(
                    text="Tavsif", callback_data=f"admin:editfield:description:{movie_number}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Video", callback_data=f"admin:editfield:file_id:{movie_number}"
                ),
                InlineKeyboardButton(
                    text="Preview", callback_data=f"admin:editfield:preview_file_id:{movie_number}"
                ),
            ],
        ]
    )


def confirm_delete_keyboard(movie_number: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha", callback_data=f"admin:delete_confirm:{movie_number}"
                ),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="admin:cancel"),
            ]
        ]
    )


def force_sub_manage_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    status_btn = "🔴 O'chirish" if enabled else "🟢 Yoqish"
    action = "admin:forcesub:off" if enabled else "admin:forcesub:on"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=status_btn, callback_data=action)],
            [InlineKeyboardButton(text="🆔 Kanal ID sozlash", callback_data="admin:forcesub:setid")],
            [InlineKeyboardButton(text="🔗 Kanal havolasi sozlash", callback_data="admin:forcesub:setlink")],
        ]
    )


def force_sub_check_keyboard(channel_link: str | None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if channel_link:
        rows.append([InlineKeyboardButton(text="📢 Kanalga o'tish", url=channel_link)])
    rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="sub:check")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
