import calendar
from datetime import date


def max_reservation_date(base_date: date) -> date:
    """Return the furthest allowed reservation date (1 calendar month ahead)."""
    if not isinstance(base_date, date):
        raise TypeError("base_date must be a date instance")

    if base_date.month == 12:
        target_year = base_date.year + 1
        target_month = 1
    else:
        target_year = base_date.year
        target_month = base_date.month + 1

    last_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(base_date.day, last_day)
    return date(target_year, target_month, target_day)
