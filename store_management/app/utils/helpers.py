from datetime import datetime
from config import DATE_FORMAT, DATETIME_FORMAT


def format_price(value: float, currency: str = "TND") -> str:
    return f"{value:.3f} {currency}"


def format_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        return datetime.fromisoformat(date_str).strftime(DATE_FORMAT)
    except Exception:
        return date_str


def format_datetime(dt_str: str) -> str:
    if not dt_str:
        return ""
    try:
        return datetime.fromisoformat(dt_str).strftime(DATETIME_FORMAT)
    except Exception:
        return dt_str


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def first_day_of_month() -> str:
    d = datetime.now()
    return d.replace(day=1).strftime("%Y-%m-%d")
