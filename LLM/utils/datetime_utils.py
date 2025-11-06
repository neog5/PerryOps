"""
DateTime utilities for computing surgical stop times from relative phrases.
"""

import re
from datetime import datetime
from typing import Optional
from datetime_subtract_tool import subtract_time


_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60
}


def _to_int(token: str) -> Optional[int]:
    """
    Convert a numeric word or digit string to an integer.
    
    Args:
        token: String representation of a number (e.g., "five", "5", "twenty-one")
        
    Returns:
        int: The numeric value, or None if conversion fails
    """
    token = (token or "").strip().lower()
    if token.isdigit():
        return int(token)
    
    # Handle hyphenated numbers like "twenty-one"
    if "-" in token:
        parts = token.split("-")
        if len(parts) == 2 and parts[0] in _NUMBER_WORDS and parts[1] in _NUMBER_WORDS:
            return _NUMBER_WORDS[parts[0]] + _NUMBER_WORDS[parts[1]]
    
    return _NUMBER_WORDS.get(token)


def _parse_surgery_datetime(surgery_details: dict) -> Optional[datetime]:
    """
    Parse surgery date and time from structured data.
    
    Args:
        surgery_details: Dict containing 'date' (YYYY-MM-DD) and optional 'time' (HH:MM)
        
    Returns:
        datetime: Parsed datetime object, or None if parsing fails
    """
    if not surgery_details:
        return None
    
    date_str = surgery_details.get("date")  # YYYY-MM-DD
    time_str = surgery_details.get("time")  # HH:MM
    
    if not date_str:
        return None
    
    try:
        if time_str:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        else:
            return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None


def compute_stop_time_datetime(surgery_details: dict, phrase: Optional[str]) -> Optional[datetime]:
    """
    Convert a relative phrase (e.g., 'five days before surgery') into an absolute datetime.
    
    Args:
        surgery_details: Dict containing surgery date and time information
        phrase: Relative time phrase (e.g., "3 days before surgery", "night before")
        
    Returns:
        datetime: Absolute datetime when the action should stop, or None if conversion not possible
    """
    if not phrase or not isinstance(phrase, str):
        return None
    
    phrase_l = phrase.strip().lower()
    anchor = _parse_surgery_datetime(surgery_details)
    
    if anchor is None:
        return None

    # Common patterns: N days/hours before/prior
    m = re.search(r"(\d+|[a-zA-Z-]+)\s+days?\s+(before|prior)", phrase_l)
    if m:
        n = _to_int(m.group(1))
        if n is not None:
            return subtract_time(anchor, days=n)

    m = re.search(r"(\d+|[a-zA-Z-]+)\s+(hours?|hrs?|hr)\s+(before|prior)", phrase_l)
    if m:
        n = _to_int(m.group(1))
        if n is not None:
            return subtract_time(anchor, hours=n)

    # Day of procedure -> use anchor date at midnight unless specific time given
    if "day of procedure" in phrase_l or phrase_l == "day of" or phrase_l == "day of surgery":
        return anchor.replace(hour=0, minute=0, second=0, microsecond=0)

    # Night before -> previous day at 21:00 (9 PM) by convention
    if "night before" in phrase_l:
        dt = subtract_time(anchor, days=1)
        return dt.replace(hour=21, minute=0, second=0, microsecond=0)

    # Morning of -> day-of at 08:00
    if "morning of" in phrase_l:
        return anchor.replace(hour=8, minute=0, second=0, microsecond=0)

    # After midnight / fasting after midnight -> day-of at 00:00
    if "after midnight" in phrase_l or phrase_l == "midnight" or "fasting after midnight" in phrase_l:
        return anchor.replace(hour=0, minute=0, second=0, microsecond=0)

    # If phrase equals 'continue' or similar, no hold -> None
    if phrase_l in {"continue", "as usual", "no change"}:
        return None

    # No match -> None (leave the phrase as-is)
    return None
