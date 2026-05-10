import os
import sys
import time
from datetime import datetime

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.adb_controller import FireStickController
from scripts.label_logger import LabelLogger
from scripts.capture_manager import CaptureManager
from scripts.config import PACKAGES, FIRESTICK_IP, NETWORK_INTERFACE

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(session_id, ip):
    print("="*60)
    print("      EDGEPULSE FIRE STICK TELEMETRY NODE")
    print("="*60)
    print(f" SESSION ID: {session_id}")
    print(f" TARGET IP:  {ip}")
    print(f" START TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

def print_menu():
    print("\n [ NAVIGATION ]          [ APPS ]             [ LABELS ]")
    print("  h: HOME                 y: YouTube           s: Mark STREAMING")
    print("  b: BACK                 n: Netflix           f: Mark BUFFERING")
    print("  e: ENTER                p: Prime Video       i: Mark IDLE")
    print("  Arrows: u, d, l, r")
    print("-" * 60)
    print("  stat: Check Foreground Activity")
    print("  q:    End Session & Save Metadata")
    print("-" * 60)

def main():
    clear_screen()
    
    # 1. Session Setup
    print("Starting new experiment session...")
    notes = input("Enter session notes/description: ")
    
    l_logger = LabelLogger()
    controller = FireStickController(label_logger=l_logger)
    capture_mgr = CaptureManager(session_id=l_logger.session_id)
    
    # 2. Connection
    if not controller.connect():
        print(f"\n[ERROR] Could not connect to Fire Stick at {FIRESTICK_IP}")
        print("Please ensure ADB is enabled and the device is on the network.")
        return

    # 3. Packet Capture Setup
    start_pcap = input(f"Start packet capture on interface '{NETWORK_INTERFACE}'? (y/n): ").lower() == 'y'
    if start_pcap:
        if not capture_mgr.start_capture():
            print("[WARNING] Packet capture failed to start. Continuing with labels only.")
            start_pcap = False

    # 4. Metadata Initialization
    metadata = {
        "target_ip": FIRESTICK_IP,
        "initial_notes": notes,
        "start_time": datetime.now().isoformat(),
        "pcap_enabled": start_pcap,
        "network_interface": NETWORK_INTERFACE if start_pcap else None
    }

    # 4. Interactive Loop
    try:
        while True:
            clear_screen()
            print_header(l_logger.session_id, FIRESTICK_IP)
            print_menu()
            
            cmd = input("Action > ").lower().strip()
            
            if cmd == 'q':
                break
            
            # Navigation
            elif cmd == 'h': controller.home()
            elif cmd == 'b': controller.back()
            elif cmd == 'e': controller.enter()
            elif cmd == 'u': controller.up()
            elif cmd == 'd': controller.down()
            elif cmd == 'l': controller.left()
            elif cmd == 'r': controller.right()
            
            # Apps
            elif cmd == 'y': controller.launch_app(PACKAGES["YOUTUBE"])
            elif cmd == 'n': controller.launch_app(PACKAGES["NETFLIX"])
            elif cmd == 'p': controller.launch_app(PACKAGES["PRIME_VIDEO"])
            
            # Manual Label Insertion
            elif cmd == 's':
                l_logger.log_event("MANUAL_MARK", controller.current_app, "streaming", "User marked as streaming")
            elif cmd == 'f':
                l_logger.log_event("MANUAL_MARK", controller.current_app, "buffering", "User marked as buffering")
            elif cmd == 'i':
                l_logger.log_event("MANUAL_MARK", controller.current_app, "idle", "User marked as idle")
            
            # Status
            elif cmd == 'stat':
                activity = controller.get_foreground_activity()
                print(f"\n[DEBUG] Foreground Activity: {activity}")
                input("\nPress Enter to continue...")
            
            else:
                if cmd:
                    print(f"\n[!] Invalid command: {cmd}")
                    time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nSession interrupted by user.")
    
    # 5. Session Wrap-up
    if start_pcap:
        capture_mgr.stop_capture()

    metadata["end_time"] = datetime.now().isoformat()
    l_logger.save_metadata(metadata)
    
    print("\n" + "="*60)
    print(" SESSION COMPLETE")
    print(f" Labels:   {l_logger.filepath}")
    if start_pcap:
        print(f" Capture:  {capture_mgr.filepath}")
    print(f" Metadata: labels/session_{l_logger.session_id}_metadata.json")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
