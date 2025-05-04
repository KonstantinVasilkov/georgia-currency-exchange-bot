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
