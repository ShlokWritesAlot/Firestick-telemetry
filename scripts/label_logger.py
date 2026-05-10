import csv
import os
import uuid
from datetime import datetime
import sys

# Add parent directory to path to allow absolute imports if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import LABEL_DIR, VALID_LABELS, LABEL_FILENAME_FORMAT
from scripts.utils import setup_logging, get_timestamp, get_unix_timestamp

logger = setup_logging("LabelLogger")

class LabelLogger:
    def __init__(self, session_id=None):
        """
        Initializes the labeling system.
        If session_id is not provided, a new one is generated.
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = LABEL_FILENAME_FORMAT.format(session_id=self.session_id)
        self.filepath = os.path.join(LABEL_DIR, self.filename)
        
        self._initialize_csv()
        logger.info(f"Initialized LabelLogger for session: {self.session_id}")

    def _initialize_csv(self):
        """
        Creates the CSV file with headers if it doesn't exist.
        """
        if not os.path.exists(LABEL_DIR):
            os.makedirs(LABEL_DIR)

        if not os.path.exists(self.filepath):
            headers = [
                "timestamp_iso",
                "timestamp_unix",
                "session_id",
                "event",
                "app",
                "label",
                "notes"
            ]
            with open(self.filepath, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.debug(f"Created label file: {self.filepath}")

    def log_event(self, event: str, app: str = "Unknown", label: str = "unknown", notes: str = ""):
        """
        Logs a timestamped event to the CSV file.
        Includes validation of the label.
        """
        if label not in VALID_LABELS:
            logger.warning(f"Invalid label provided: {label}. Defaulting to 'unknown'.")
            label = "unknown"

        row = [
            get_timestamp(),
            get_unix_timestamp(),
            self.session_id,
            event,
            app,
            label,
            notes
        ]

        try:
            with open(self.filepath, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            logger.info(f"Label logged: {event} | {app} | {label}")
        except Exception as e:
            logger.error(f"Failed to log label: {str(e)}")

    def validate_label(self, label: str):
        """Helper to check if a label is valid."""
        return label in VALID_LABELS

if __name__ == "__main__":
    # Test labeling system
    l_logger = LabelLogger()
    l_logger.log_event("test_event", "Netflix", "streaming", "Initial test log")
    l_logger.log_event("home_press", "Launcher", "idle", "Pressed home button")
