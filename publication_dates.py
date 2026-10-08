"""Publication calendar dates; retain the source's calendar day, not an event date."""
from datetime import date, datetime
from email.utils import parsedate_to_datetime


def publication_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
    except ValueError:
        try:
            return parsedate_to_datetime(value).date()
        except (ValueError, TypeError, OverflowError):
            return None


def validate_range(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise ValueError('The start date must be on or before the end date.')


def exclusion_reason(published, start_date=None, end_date=None, include_undated=True):
    validate_range(start_date, end_date)
    if not start_date and not end_date:
        return None
    if published is None:
        return None if include_undated else 'unknown_date'
    if (start_date and published < start_date) or (end_date and published > end_date):
        return 'outside_range'
    return None
