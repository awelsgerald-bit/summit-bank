from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Numeric, DateTime

from app.database import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String(10), unique=True, nullable=False)  # "BTC"
    rate_usd = Column(Numeric(20, 2), nullable=False)  # 1 unit of currency = this many USD
    source = Column(String(20), nullable=False, default="coingecko")  # "coingecko" or "manual"
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))