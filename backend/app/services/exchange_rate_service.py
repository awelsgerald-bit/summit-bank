import httpx
from sqlalchemy.orm import Session

from app.models.exchange_rate import ExchangeRate

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
CURRENCY_TO_COINGECKO_ID = {"BTC": "bitcoin"}


def fetch_live_rate(currency: str) -> float:
    coingecko_id = CURRENCY_TO_COINGECKO_ID[currency]
    response = httpx.get(
        COINGECKO_URL,
        params={"ids": coingecko_id, "vs_currencies": "usd"},
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()
    return data[coingecko_id]["usd"]


def get_current_rate(db: Session, currency: str) -> ExchangeRate:
    """
    Returns the current rate for a currency. Tries CoinGecko first;
    falls back to whatever's cached in the DB (e.g. a manual admin override,
    or the last successfully fetched rate) if the live call fails.
    """
    rate_row = db.query(ExchangeRate).filter(ExchangeRate.currency == currency).first()

    try:
        live_rate = fetch_live_rate(currency)
        if rate_row:
            rate_row.rate_usd = live_rate
            rate_row.source = "coingecko"
        else:
            rate_row = ExchangeRate(currency=currency, rate_usd=live_rate, source="coingecko")
            db.add(rate_row)
        db.commit()
        db.refresh(rate_row)
        return rate_row
    except (httpx.HTTPError, KeyError):
        if rate_row:
            return rate_row  # fall back to last known rate (live or manually set)
        raise