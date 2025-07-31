# config_utils.py
import json

CONFIG_FILE = "standup_profile.json"
_cfg_cache = None  # Use an internal cache for performance and consistency


def validate_standup_config(cfg):
    required_fields = {
        "standup_time": "standup time",
        "timezone": "timezone",
        "standup_days": "standup days",
        "standup_channel_id": "announcement channel",
        "standup_role_id": "standup role",
        "standup_title": "standup title",
        "standup_questions": "standup questions",
    }

    missing = []

    for key, label in required_fields.items():
        value = cfg.get(key)
        if value is None or (isinstance(value, (list, str)) and not value):
            missing.append(label)

    is_valid = len(missing) == 0
    return is_valid, missing


def load_config():
    global _cfg_cache
    if _cfg_cache is None:  # Load only once
        try:
            with open(CONFIG_FILE, "r") as f:
                _cfg_cache = json.load(f)
        except FileNotFoundError:
            # Initialize with default values if file doesn't exist
            _cfg_cache = {
                "toggled": False,
                "standup_time": [9, 0, "09:00"],
                "timezone": "UTC+0",
                "standup_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "standup_channel_id": None,
                "standup_role_id": None,
                "standup_title": "Daily Standup",
                "standup_desc": "Please answer the following questions:",
                "standup_questions": [
                    "What did you do yesterday?",
                    "What will you do today?",
                    "Are there any blockers?"
                ],
                "tickets_channel_id": None,
            }
            save_config_changes(_cfg_cache)  # Save initial config
    return _cfg_cache


def save_config_changes(cfg_data):  # <--- Accepts cfg_data as an argument
    global _cfg_cache
    _cfg_cache = cfg_data  # Update the internal cache with the data being saved
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg_data, f, indent=2)
    print('     ◈ Config save successful')
