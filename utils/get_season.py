from datetime import datetime


def get_current_season() -> str:
    """Returns current season — if before August, returns previous year."""
    year = datetime.now().year
    month = datetime.now().month
    return str(year) if month >= 8 else str(year - 1)


def get_season_from_date(date: datetime) -> str:
    """Returns season year from a given date."""
    return str(date.year) if date.month >= 8 else str(date.year - 1)