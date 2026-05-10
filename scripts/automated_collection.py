import time
import os
import sys
from datetime import datetime

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.adb_controller import FireStickController
from scripts.label_logger import LabelLogger
from scripts.capture_manager import CaptureManager
from scripts.config import FIRESTICK_IP

def run_automated_session(name, duration, res="Auto", wifi="Good", action_fn=None):
    print(f"\n>>> STARTING GOLD STANDARD SESSION: {name} ({res}) - {duration}s")
    
    l_logger = LabelLogger()
    controller = FireStickController(label_logger=l_logger)
    capture_mgr = CaptureManager(session_id=l_logger.session_id)
    
    if not controller.connect():
        print(f"Failed to connect for {name}")
        return
    
    # Start Capture
    if not capture_mgr.start_capture():
        print(f"Capture failed to start for {name}")
        return

    metadata = {
        "target_ip": FIRESTICK_IP,
        "initial_notes": f"Automated Gold Standard {name} session",
        "target_resolution": res,
        "wifi_strength": wifi,
        "start_time": datetime.now().isoformat()
    }

    try:
        # GOLD STANDARD: Initial Cooldown (5s)
        print("Cooldown: Waiting 5 seconds before starting events...")
        time.sleep(5)
        
        if action_fn:
            action_fn(controller)
        
        print(f"Collecting data for {duration} seconds...")
        time.sleep(duration)
        
        # GOLD STANDARD: Ending Cooldown (5s)
        print("Cooldown: Waiting 5 seconds before ending session...")
        time.sleep(5)
        
    except Exception as e:
        print(f"Error during {name}: {e}")
    finally:
        capture_mgr.stop_capture()
        l_logger.save_metadata(metadata)
        print(f">>> SESSION COMPLETE: {name}")
    
    return l_logger.session_id

def idle_action(controller):
    controller.home()
    time.sleep(2)
    controller.label_logger.log_event("IDLE_START", label="idle")

def launch_youtube_action(controller):
    controller.launch_app("com.amazon.firetv.youtube")
    time.sleep(5)
    controller.label_logger.log_event("APP_READY", label="idle")

def streaming_action(controller):
    controller.launch_app("com.amazon.firetv.youtube")
    time.sleep(10)
    controller.enter() # Play
    time.sleep(5) # Buffer cooldown
    controller.label_logger.log_event("STREAMING_START", label="streaming")

def paused_action(controller):
    controller.launch_app("com.amazon.firetv.youtube")
    time.sleep(10)
    controller.enter() # Play
    time.sleep(10) # Stream for a bit
    controller.enter() # Pause
    time.sleep(2)
    controller.label_logger.log_event("PAUSE_MARK", label="paused_stream")

if __name__ == "__main__":
    sessions = []
    
    # 1. IDLE
    sessions.append(run_automated_session("IDLE", 30))
    
    # 2. STREAMING 480p (Simulated by label)
    sessions.append(run_automated_session("STREAMING_480p", 45, res="480p"))
    
    # 3. STREAMING 1080p (Simulated by label)
    sessions.append(run_automated_session("STREAMING_1080p", 45, res="1080p"))
    
    # 4. PAUSED_STREAM
    sessions.append(run_automated_session("PAUSED", 20, action_fn=paused_action))
    
    print("\n" + "="*40)
    print(" GOLD STANDARD COLLECTION COMPLETE")
    print(f" Sessions: {sessions}")
    print("="*40)
