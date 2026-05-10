import subprocess
import time
import sys
import os

# Add parent directory to path to allow absolute imports if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import FIRESTICK_IP, ADB_PATH, KEY_CODES, PACKAGES
from scripts.utils import setup_logging, get_timestamp
from scripts.label_logger import LabelLogger

logger = setup_logging("ADBController")

class FireStickController:
    def __init__(self, ip=FIRESTICK_IP, label_logger=None):
        self.ip = ip
        self.adb_cmd = ADB_PATH
        self.connected = False
        self.label_logger = label_logger
        self.current_app = "Unknown"

    def _run_command(self, cmd_args):
        """
        Executes an ADB command safely.
        """
        full_cmd = [self.adb_cmd] + cmd_args
        try:
            logger.debug(f"Executing: {' '.join(full_cmd)}")
            result = subprocess.run(
                full_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                timeout=10
            )
            if result.returncode != 0:
                logger.error(f"Command failed: {result.stderr.strip()}")
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(full_cmd)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error executing command: {str(e)}")
            return None

    def connect(self):
        """
        Connects to the FireStick over ADB via IP.
        """
        logger.info(f"Attempting to connect to {self.ip}...")
        # First disconnect to clear any stale sessions
        self._run_command(["disconnect", self.ip])
        
        result = self._run_command(["connect", self.ip])
        if result and "connected to" in result.stdout:
            logger.info(f"Successfully connected to {self.ip}")
            self.connected = True
            return True
        else:
            logger.error(f"Failed to connect to {self.ip}")
            self.connected = False
            return False

    def send_key(self, key_name):
        """
        Sends a key event to the FireStick.
        """
        if key_name not in KEY_CODES:
            logger.warning(f"Unknown key: {key_name}")
            return False

        code = KEY_CODES[key_name]
        logger.info(f"[{get_timestamp()}] Sending KEY_{key_name} ({code})")
        
        result = self._run_command(["-s", self.ip, "shell", "input", "keyevent", str(code)])
        
        if self.label_logger:
            self.label_logger.log_event(
                event=f"KEY_{key_name}", 
                app=self.current_app, 
                label="idle" if key_name in ["HOME", "BACK"] else "unknown"
            )
            
        return result is not None and result.returncode == 0

    def launch_app(self, package_name):
        """
        Launches an app using its package name.
        """
        logger.info(f"[{get_timestamp()}] Launching app: {package_name}")
        self.current_app = package_name
        
        # monkey -p <package> -c android.intent.category.LAUNCHER 1 is a reliable way to launch
        result = self._run_command([
            "-s", self.ip, 
            "shell", "monkey", 
            "-p", package_name, 
            "-c", "android.intent.category.LAUNCHER", 
            "1"
        ])
        
        if self.label_logger:
            self.label_logger.log_event(
                event="APP_LAUNCH", 
                app=package_name, 
                label="app_launch"
            )
            
        return result is not None and result.returncode == 0

    def get_foreground_activity(self):
        """
        Queries the current foreground activity.
        Useful for labeling workloads.
        """
        # Command varies slightly by Android version, but this is generally reliable
        result = self._run_command([
            "-s", self.ip, 
            "shell", "dumpsys", "window", "windows", "|", "grep", "-E", "'mCurrentFocus|mFocusedApp'"
        ])
        
        if result and result.stdout:
            activity = result.stdout.strip()
            logger.debug(f"Foreground Activity: {activity}")
            return activity
        return "Unknown"

    # Shortcuts for common actions
    def home(self): return self.send_key("HOME")
    def back(self): return self.send_key("BACK")
    def enter(self): return self.send_key("ENTER")
    def up(self): return self.send_key("UP")
    def down(self): return self.send_key("DOWN")
    def left(self): return self.send_key("LEFT")
    def right(self): return self.send_key("RIGHT")

if __name__ == "__main__":
    # Initialize labeling system
    l_logger = LabelLogger()
    
    # Initialize controller with labeling support
    controller = FireStickController(label_logger=l_logger)
    
    if controller.connect():
        print("\n--- EdgePulse FireStick Telemetry Node (w/ Labeling) ---")
        print(f"Connected to: {controller.ip}")
        print(f"Session ID: {l_logger.session_id}")
        
        # Example: controller.home()
        # This will automatically log the event to labels/session_<id>_labels.csv
    else:
        print("Could not connect. Please check IP and ensure ADB is enabled on FireStick.")
