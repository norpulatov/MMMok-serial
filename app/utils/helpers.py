from datetime import datetime


def format_movie_details(
    number: int,
    title: str,
    description: str | None,
    views: int,
    added_at: datetime | None,
) -> str:
    date_text = added_at.strftime("%Y-%m-%d %H:%M") if added_at else "Noma'lum"
    desc = description if description else "Tavsif yo'q"
    return (
        f"🎬 #{number} - {title}\n\n"
        f"📝 Tavsif: {desc}\n"
        f"👁 Ko'rilganlar: {views}\n"
        f"📅 Qo'shilgan sana: {date_text}"
    )


def short_description(text: str | None, max_len: int = 50) -> str:
    if not text:
        return "Tavsif yo'q"
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
