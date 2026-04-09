from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Movie(Base):
    __tablename__ = 'movies'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[str] = mapped_column(String(512))
    preview_file_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Telegram kanalidagi e'lon posti message_id
    channel_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    channel_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    added_by: Mapped[int] = mapped_column(BigInteger)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    views_count: Mapped[int] = mapped_column(Integer, default=0, server_default='0')


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    force_sub_enabled: Mapped[bool] = mapped_column(default=False, server_default="0")
    force_sub_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    force_sub_channel_link: Mapped[str | None] = mapped_column(String(512), nullable=True)


class MoviePart(Base):
    __tablename__ = "movie_parts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(Integer, index=True)
    part_number: Mapped[int] = mapped_column(Integer)
    file_id: Mapped[str] = mapped_column(String(512))
