"""
Utility functions for parsing schedule data.
"""

from typing import List, Dict, Any


def parse_time_to_minutes(time_str: str) -> int:
    """
    Convert time string (HH:MM) to minutes from midnight.

    Args:
        time_str: Time string in format "HH:MM"

    Returns:
        int: Number of minutes from midnight
    """
    hour, minute = map(int, time_str.split(":"))
    return hour * 60 + minute


def parse_day_to_int(day_name: str) -> int:
    """
    Convert day name to integer (0-6, where 0 is Monday).

    Args:
        day_name: Day name in English

    Returns:
        int: Day number (0-6)
    """
    days = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }
    return days.get(day_name, 0)


def parse_schedule(schedule_data: List[Dict[str, Any]]) -> List[Dict[str, int]]:
    """
    Parse schedule data from API response to list of schedule entries.

    Args:
        schedule_data: List of schedule entries from API

    Returns:
        List[Dict[str, int]]: List of parsed schedule entries
    """
    parsed_schedules = []

    for entry in schedule_data:
        start_day = parse_day_to_int(entry["start"]["en"])
        end_day = (
            parse_day_to_int(entry["end"]["en"])
            if entry.get("end") and entry["end"].get("en")
            else start_day
        )

        for interval in entry["intervals"]:
            start_time, end_time = interval.split("-")
            opens_at = parse_time_to_minutes(start_time)
            closes_at = parse_time_to_minutes(end_time)

            # Handle 24/7 case
            if opens_at == 0 and closes_at == 0:
                opens_at = 0
                closes_at = 24 * 60  # 24 hours in minutes

            # Create entries for each day in the range
            current_day = start_day
            while current_day <= end_day:
                parsed_schedules.append(
                    {
                        "day": current_day,
                        "opens_at": opens_at,
                        "closes_at": closes_at,
                    }
                )
                current_day += 1

    return parsed_schedules


def minutes_to_time_str(minutes: int) -> str:
    """
    Convert minutes from midnight to HH:MM string.
    """
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def format_weekly_schedule(schedules: list[dict[str, int]]) -> str:
    """
    Format a list of schedule dicts into a human-readable weekly schedule string.
    Args:
        schedules: List of dicts with 'day', 'opens_at', 'closes_at'.
    Returns:
        str: Formatted schedule string.
    """
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    # Group by (opens_at, closes_at)
    by_hours: dict[tuple[int, int], list[int]] = {}
    for entry in schedules:
        key = (entry["opens_at"], entry["closes_at"])
        by_hours.setdefault(key, []).append(entry["day"])
    lines = []
    for (opens, closes), day_list in sorted(by_hours.items(), key=lambda x: x[1][0]):
        # Group consecutive days
        day_list = sorted(day_list)
        ranges = []
        start = prev = day_list[0]
        for d in day_list[1:]:
            if d == prev + 1:
                prev = d
            else:
                ranges.append((start, prev))
                start = prev = d
        ranges.append((start, prev))
        for start, end in ranges:
            if opens == closes:
                hours = "Closed"
            elif opens == 0 and closes == 24 * 60:
                hours = "Open 24/7"
            else:
                hours = f"{minutes_to_time_str(opens)}-{minutes_to_time_str(closes)}"
            if start == end:
                day_str = days[start]
            else:
                day_str = f"{days[start]}-{days[end]}"
            lines.append(f"{day_str}: {hours}")
    return "\n".join(lines)
