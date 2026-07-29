from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str


class SourceBase(BaseModel):
    name: str
    url: str
    source_type: str = "css"
    value_selector: str
    news_selector: Optional[str] = None
    priority: int = 1
    active: bool = True


class SourceCreate(SourceBase):
    item_id: int


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    value_selector: Optional[str] = None
    news_selector: Optional[str] = None
    priority: Optional[int] = None
    active: Optional[bool] = None


class SourceOut(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int


class ItemBase(BaseModel):
    code: str
    name: str
    category: str
    unit: str = "USD/bbl"
    active: bool = True


class ItemCreate(ItemBase):
    pass


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sources: List[SourceOut] = []


class NavItem(BaseModel):
    code: str
    name: str


class NavCategory(BaseModel):
    category: str
    items: List[NavItem]


class PricePoint(BaseModel):
    price_date: date
    price: float


class TickerEntry(BaseModel):
    code: str
    name: str
    category: str
    unit: str
    current_price: Optional[float] = None
    previous_price: Optional[float] = None
    daily_change: Optional[float] = None
    daily_change_pct: Optional[float] = None
    as_of: Optional[date] = None


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    headline: str
    url: Optional[str] = None
    source: Optional[str] = None
    collected_at: datetime


class ItemDetail(BaseModel):
    code: str
    name: str
    category: str
    unit: str
    current_price: Optional[float] = None
    previous_price: Optional[float] = None
    daily_change: Optional[float] = None
    daily_change_pct: Optional[float] = None
    as_of: Optional[date] = None
    weekly_series: List[PricePoint] = []
    monthly_series: List[PricePoint] = []
    news: List[NewsOut] = []


class ScrapeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    run_at: datetime
    item_code: Optional[str] = None
    source_name: Optional[str] = None
    status: str
    message: Optional[str] = None


class ScrapeSettingOut(BaseModel):
    frequency_minutes: int


class ScrapeSettingUpdate(BaseModel):
    frequency_minutes: int


class AIAskRequest(BaseModel):
    provider: str  # "deepseek" | "claude"
    item_code: Optional[str] = None
    question: str


class AIAskResponse(BaseModel):
    provider: str
    answer: str


class AICredentialsOut(BaseModel):
    deepseek_configured: bool
    claude_configured: bool


class AICredentialsUpdate(BaseModel):
    deepseek_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
