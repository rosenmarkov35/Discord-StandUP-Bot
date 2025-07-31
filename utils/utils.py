import re
from datetime import timezone, timedelta, datetime

import discord


async def user_has_role(interaction: discord.Interaction, role_name: str) -> bool:
    guild = interaction.guild
    print(f"[user_has_role] guild: {guild}")  # debug
    if not guild:
        print("[user_has_role] → no guild")
        return False

    try:
        member = await guild.fetch_member(interaction.user.id)
    except discord.NotFound:
        print("[user_has_role] → member not found")
        return False

    has = any(r.name == role_name for r in member.roles)
    print(f"[user_has_role] roles of {member}: {[r.name for r in member.roles]}, has {role_name}? {has}")
    return has


def get_timezone_from_string(utc_str):
    match = re.match(r"^UTC([+-])(\d{1,2})(?::([03]0))?$", utc_str)
    if not match:
        raise ValueError("Invalid timezone format.")

    sign, hours_str, minutes_str = match.groups()
    hours = int(hours_str)
    minutes = int(minutes_str) if minutes_str else 0

    offset_minutes = hours * 60 + minutes
    if sign == "-":
        offset_minutes = -offset_minutes

    return timezone(timedelta(minutes=offset_minutes))


def get_time_until_next_standup(cfg):
    if not (cfg["standup_time"] and cfg["standup_days"] and cfg["timezone"]):
        return None

    hour, minute = map(int, cfg["standup_time"][2].split(":"))
    offset = get_timezone_from_string(cfg["timezone"])

    now_local = datetime.now(offset)

    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_indexes = [weekdays.index(day.lower()) for day in cfg["standup_days"] if day.lower() in weekdays]

    # Today’s weekday index (0=Monday, 6=Sunday)
    today_idx = now_local.weekday()

    # Check if today is a standup day and the time hasn't passed yet
    for delta in range(0, 7):
        check_day = (today_idx + delta) % 7
        if check_day in day_indexes:
            standup_dt = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=delta)
            if standup_dt > now_local:
                return standup_dt - now_local

    # Fallback: next week's first valid day
    next_day_idx = min(day_indexes)
    days_until = (next_day_idx - today_idx + 7) % 7 or 7
    standup_dt = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_until)
    return standup_dt - now_local
