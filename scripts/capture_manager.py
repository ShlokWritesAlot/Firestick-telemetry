import subprocess
import os
import signal
import time
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import TSHARK_PATH, NETWORK_INTERFACE, CAPTURE_DIR, FIRESTICK_IP
from scripts.utils import setup_logging

logger = setup_logging("CaptureManager")

class CaptureManager:
    def __init__(self, session_id: str, interface: str = NETWORK_INTERFACE):
        self.session_id = session_id
        self.interface = interface
        self.process = None
        self.filename = f"session_{session_id}_capture.pcapng"
        self.filepath = os.path.join(CAPTURE_DIR, self.filename)
        
        if not os.path.exists(CAPTURE_DIR):
            os.makedirs(CAPTURE_DIR)

    def start_capture(self, target_ip: str = FIRESTICK_IP):
        """
        Starts a tshark capture in the background.
        Filters for the target IP to keep files clean.
        """
        if self.process:
            logger.warning("Capture already running.")
            return False

        # Build tshark command
        # -i: interface
        # -f: capture filter (BPF) - captures traffic to/from the target IP
        # -w: output file
        cmd = [
            TSHARK_PATH,
            "-i", self.interface,
            "-f", f"host {target_ip}",
            "-w", self.filepath
        ]

        try:
            logger.info(f"Starting packet capture on interface {self.interface} for IP {target_ip}...")
            # We use a subprocess to keep it running in the background
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Give it a second to start
            time.sleep(2)
            
            if self.process.poll() is not None:
                # Process ended immediately, likely an error
                _, stderr = self.process.communicate()
                logger.error(f"TShark failed to start: {stderr.strip()}")
                return False
            
            logger.info(f"Capture started: {self.filepath}")
            return True
            
        except FileNotFoundError:
            logger.error(f"TShark binary not found at '{TSHARK_PATH}'. Please install Wireshark/TShark.")
            return False
        except Exception as e:
            logger.error(f"Error starting capture: {str(e)}")
            return False

    def stop_capture(self):
        """
        Stops the running tshark capture.
        """
        if not self.process:
            logger.warning("No capture process to stop.")
            return

        logger.info("Stopping packet capture...")
        try:
            # On Windows, we need to be careful with terminating subprocesses
            # subprocess.terminate() is usually enough for tshark
            self.process.terminate()
            self.process.wait(timeout=5)
            logger.info(f"Capture stopped. File saved: {self.filepath}")
        except subprocess.TimeoutExpired:
            logger.warning("TShark didn't stop gracefully, killing process...")
            self.process.kill()
        except Exception as e:
            logger.error(f"Error stopping capture: {str(e)}")
        finally:
            self.process = None

if __name__ == "__main__":
    # Quick test
    cm = CaptureManager("test_run")
    if cm.start_capture():
        print("Capturing for 5 seconds...")
        time.sleep(5)
        cm.stop_capture()
    else:
        print("Failed to start capture.")
