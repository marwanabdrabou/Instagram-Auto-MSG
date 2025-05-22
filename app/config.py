from datetime import time
import os

# Directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
INPUT_DIR = os.path.join(DATA_DIR, 'input')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

# Create directories if they don't exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# File paths
RESULTS_FILE = os.path.join(OUTPUT_DIR, 'message_results.csv')

# Browser settings
CHROME_OPTIONS = {
    "profile.default_content_setting_values.notifications": 2,
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.javascript": 1
}

# Default application settings
DEFAULT_SETTINGS = {
    'max_messages': 48,
    'time_interval': 600,  # seconds between batches
    'cooldown_min': 5,     # minutes
    'cooldown_max': 15,    # minutes
    'message_delay': (10, 30)  # min and max seconds between messages
}

# Instagram selectors (updated for current Instagram UI)
SELECTORS = {
    'login_page': {
        'username_field': "//input[@name='username']",
        'password_field': "//input[@name='password']",
        'submit_button': "//button[@type='submit']",
        'not_now_button': "//button[contains(text(), 'Not Now')]"
    },
    'profile_page': {
        'message_button': [
            "//div[contains(@class, 'x1q0g3np') and contains(text(), 'Message')]",
            "//div[contains(text(), 'Message')]"
        ],
        'message_box': "//div[@role='textbox']",
        'send_button': "//div[contains(text(), 'Send')]"
    }
}