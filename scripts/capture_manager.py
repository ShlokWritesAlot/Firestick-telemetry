import subprocess
import os
import signal
import time
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import (
    TSHARK_PATH, CAPTURE_INTERFACE, CAPTURE_DIR, FIRESTICK_IP, FIRESTICK_MAC,
    GATEWAY_MODE, EXCLUDE_ADB_TRAFFIC, INCLUDE_IPV6
)
from scripts.utils import setup_logging

logger = setup_logging("CaptureManager")

class CaptureManager:
    def __init__(self, session_id: str, interface: str = CAPTURE_INTERFACE):
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
        Supports Gateway Mode, IPv6, and ADB filtering.
        """
        if self.process:
            logger.warning("Capture already running.")
            return False

        # Build BPF filter
        # Hardware-level filtering is the most reliable
        if FIRESTICK_MAC:
            bpf_filter = f"ether host {FIRESTICK_MAC}"
        else:
            bpf_filter = f"host {target_ip}"
            if not INCLUDE_IPV6:
                bpf_filter = f"ip host {target_ip}"
            
        if EXCLUDE_ADB_TRAFFIC:
            bpf_filter += " and not tcp port 5555"

        # Build tshark command
        cmd = [
            TSHARK_PATH,
            "-i", str(self.interface),
            "-f", bpf_filter,
            "-w", self.filepath
        ]

        try:
            print(f"\n[CAPTURE] Initializing Gateway Mode Capture...")
            print(f"[CAPTURE] Interface: {self.interface}")
            print(f"[CAPTURE] Filter:    {bpf_filter}")
            print(f"[CAPTURE] Command:   {' '.join(cmd)}")
            
            logger.info(f"Starting Gateway Mode capture on interface {self.interface}...")
            logger.info(f"Command: {' '.join(cmd)}")
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
