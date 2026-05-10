import subprocess
import argparse
import os
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import TSHARK_PATH, FIRESTICK_IP

def run_tshark_count(pcap_path, display_filter):
    """Runs tshark with a display filter and returns the packet count."""
    cmd = [
        TSHARK_PATH,
        "-r", pcap_path,
        "-Y", display_filter,
        "-T", "fields",
        "-e", "frame.number"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return len([l for l in lines if l])
        return 0
    except Exception:
        return 0

def run_tshark_top_ips(pcap_path, firestick_ip, limit=5):
    """Returns top destination IPs from the capture."""
    cmd = [
        TSHARK_PATH,
        "-r", pcap_path,
        "-Y", f"ip.src == {firestick_ip}",
        "-T", "fields",
        "-e", "ip.dst"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            ips = result.stdout.strip().split('\n')
            counts = {}
            for ip in ips:
                if ip: counts[ip] = counts.get(ip, 0) + 1
            sorted_ips = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            return sorted_ips[:limit]
        return []
    except Exception:
        return []

def validate_pcap(pcap_path, firestick_ip):
    if not os.path.exists(pcap_path):
        return {"error": f"File not found: {pcap_path}"}

    print(f"Validating capture: {pcap_path}")
    
    # Define filters
    filters = {
        "total": "frame",
        "adb": "tcp.port == 5555",
        "dns": "dns",
        "tls": "tls",
        "udp": "udp",
        "tcp": "tcp",
        "quic": "quic or udp.port == 443"
    }

    stats = {}
    for name, filt in filters.items():
        count = run_tshark_count(pcap_path, filt)
        stats[name] = count

    stats["non_adb"] = stats["total"] - stats["adb"]
    stats["top_ips"] = run_tshark_top_ips(pcap_path, firestick_ip)
    
    # Verdict logic
    # If non-ADB traffic is very low compared to total, or basically zero
    if stats["non_adb"] < 50 and stats["total"] > 0:
        stats["verdict"] = "ADB_ONLY_OR_INSUFFICIENT_CAPTURE"
    elif stats["total"] == 0:
        stats["verdict"] = "EMPTY_CAPTURE"
    else:
        stats["verdict"] = "VALID_WORKLOAD_CAPTURE"

    return stats

def main():
    parser = argparse.ArgumentParser(description="Validate FireStick Telemetry Capture")
    parser.add_argument("--pcap", required=True, help="Path to pcapng file")
    parser.add_argument("--firestick-ip", default=FIRESTICK_IP, help="FireStick IP address")
    args = parser.parse_args()

    results = validate_pcap(args.pcap, args.firestick_ip)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        sys.exit(1)

    report = [
        "="*40,
        " CAPTURE VALIDATION REPORT",
        "="*40,
        f"File:           {os.path.basename(args.pcap)}",
        f"Total Packets:  {results['total']}",
        f"ADB Packets:    {results['adb']}",
        f"Non-ADB:        {results['non_adb']}",
        "-"*40,
        f"DNS Packets:    {results['dns']}",
        f"TLS Packets:    {results['tls']}",
        f"UDP Packets:    {results['udp']}",
        f"TCP Packets:    {results['tcp']}",
        f"QUIC Packets:   {results['quic']}",
        "-"*40,
        "TOP DESTINATION IPs (from FireStick):"
    ]

    for ip, count in results["top_ips"]:
        report.append(f"  {ip:<15} : {count} pkts")

    report.extend([
        "="*40,
        f"VERDICT: {results['verdict']}",
        "="*40
    ])

    if results["verdict"] != "VALID_WORKLOAD_CAPTURE":
        report.append("\nWARNING: Capture contains mostly ADB control traffic.")
        report.append("Your WiFi adapter may not be seeing Fire Stick internet traffic.")
        report.append("Try Ethernet, router-side capture, or a different capture interface.")

    final_report = "\n".join(report)
    print(final_report)
    return final_report

if __name__ == "__main__":
    main()
