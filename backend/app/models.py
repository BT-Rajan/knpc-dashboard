from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, Date,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    code = Column(String(40), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    category = Column(String(40), nullable=False)  # "Crude" | "Products"
    unit = Column(String(40), default="USD/bbl")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sources = relationship("Source", back_populates="item", cascade="all, delete-orphan")
    prices = relationship("PriceHistory", back_populates="item", cascade="all, delete-orphan")
    news = relationship("NewsItem", back_populates="item", cascade="all, delete-orphan")


class Source(Base):
    """A scrape source configured against one item, with a fallback priority."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    name = Column(String(120), nullable=False)
    url = Column(String(500), nullable=False)
    # 'css' -> value_selector picks text off the page
    # 'json_path' -> dotted path into a JSON response (e.g. yahoo chart api)
    # 'regex' -> first capture group of value_selector applied to raw text
    source_type = Column(String(20), nullable=False, default="css")
    value_selector = Column(String(500), nullable=False)
    news_selector = Column(String(500), nullable=True)  # optional: css selector for headline links
    priority = Column(Integer, default=1)  # lower = tried first
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="sources")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    price_date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("item_id", "price_date", name="uq_item_price_date"),
    )


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)  # null = general market news
    headline = Column(String(500), nullable=False)
    url = Column(String(700), nullable=True)
    source = Column(String(120), nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="news")

    __table_args__ = (
        UniqueConstraint("headline", "item_id", name="uq_headline_item"),
    )


class ScrapeLog(Base):
    __tablename__ = "scrape_log"

    id = Column(Integer, primary_key=True)
    run_at = Column(DateTime, default=datetime.utcnow)
    item_code = Column(String(40), nullable=True)
    source_name = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False)  # success | error
    message = Column(Text, nullable=True)


class ScrapeSetting(Base):
    __tablename__ = "scrape_settings"

    id = Column(Integer, primary_key=True)
    frequency_minutes = Column(Integer, default=30)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AICredentials(Base):
    """Admin-entered API keys, persisted in the DB so they survive without
    env vars / a restart. Single-row table (id=1)."""
    __tablename__ = "ai_credentials"

    id = Column(Integer, primary_key=True)
    deepseek_api_key = Column(String(200), nullable=True)
    claude_api_key = Column(String(200), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
