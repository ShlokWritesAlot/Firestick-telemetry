import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ADB Configuration
FIRESTICK_IP = os.getenv("FIRESTICK_IP", "192.168.1.100")
ADB_PATH = os.getenv("ADB_PATH", "adb")  # Assumes adb is in PATH

# TShark Configuration
TSHARK_PATH = os.getenv("TSHARK_PATH", "tshark")
NETWORK_INTERFACE = os.getenv("NETWORK_INTERFACE", "1")  # Default to first interface
INCLUDE_ADB_TRAFFIC = os.getenv("INCLUDE_ADB_TRAFFIC", "false").lower() == "true"

# Directory Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LABEL_DIR = os.path.join(BASE_DIR, "labels")
CAPTURE_DIR = os.path.join(BASE_DIR, "captures")

# Common Package Names
PACKAGES = {
    "NETFLIX": "com.netflix.ninja",
    "YOUTUBE": "com.amazon.firetv.youtube",
    "PRIME_VIDEO": "com.amazon.avod",
    "HULU": "com.hulu.plus",
    "DISNEY_PLUS": "com.disney.disneyplus"
}

# Key Event Codes (Android)
KEY_CODES = {
    "HOME": 3,
    "BACK": 4,
    "ENTER": 66,
    "UP": 19,
    "DOWN": 20,
    "LEFT": 21,
    "RIGHT": 22,
    "PLAY_PAUSE": 85,
    "MENU": 82
}

# Label Configuration
VALID_LABELS = [
    "idle",
    "app_launch",
    "streaming",
    "buffering",
    "app_switch",
    "unknown"
]

# Session Settings
SESSION_PREFIX = "session"
LABEL_FILENAME_FORMAT = "session_{session_id}_labels.csv"
