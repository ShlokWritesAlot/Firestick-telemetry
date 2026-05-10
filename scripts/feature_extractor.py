import subprocess
import os
import sys
import pandas as pd
import numpy as np
import time
from datetime import datetime

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import TSHARK_PATH, FEATURE_DIR, FIRESTICK_IP
from scripts.utils import setup_logging

logger = setup_logging("FeatureExtractor")

class FeatureExtractor:
    def __init__(self, pcap_path: str):
        self.pcap_path = pcap_path
        if not os.path.exists(FEATURE_DIR):
            os.makedirs(FEATURE_DIR, exist_ok=True)
        
        parts = os.path.basename(pcap_path).split('_')
        self.session_id = f"{parts[1]}_{parts[2]}"
        self.output_csv = os.path.join(FEATURE_DIR, f"session_{self.session_id}_features.csv")

    def _export_packets_to_df(self):
        """Uses tshark to export raw packet data to a pandas DataFrame."""
        logger.info(f"Exporting packets from {os.path.basename(self.pcap_path)}...")
        
        # Fields to extract:
        # frame.time_relative: time since start of capture
        # frame.len: packet size
        # ip.src/dst: IPs
        # tcp.srcport/dstport: ports
        # _ws.col.Protocol: protocol name
        fields = [
            "-e", "frame.time_relative",
            "-e", "frame.len",
            "-e", "ip.proto",
            "-e", "tcp.srcport",
            "-e", "udp.srcport",
            "-e", "_ws.col.Protocol"
        ]
        
        cmd = [
            TSHARK_PATH,
            "-r", self.pcap_path,
            "-T", "fields",
            "-E", "header=y",
            "-E", "separator=,",
            "-E", "quote=d"
        ] + fields

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            from io import StringIO
            df = pd.read_csv(StringIO(result.stdout))
            
            # Clean column names
            df.columns = [
                'time_relative', 'length', 'proto_id', 
                'tcp_port', 'udp_port', 'protocol'
            ]
            return df
        except Exception as e:
            logger.error(f"Error exporting packets: {str(e)}")
            return None

    def extract_features(self, window_size=1.0, step_size=0.5):
        """
        Extracts statistical features using a sliding window.
        - window_size: size of the time window in seconds
        - step_size: step between windows in seconds
        """
        df = self._export_packets_to_df()
        if df is None or df.empty:
            logger.warning("No packets to process.")
            return None

        logger.info(f"Extracting features (window={window_size}s, step={step_size}s)...")
        
        max_time = df['time_relative'].max()
        features_list = []
        
        start_time = 0
        window_history = []
        
        while start_time + window_size <= max_time:
            end_time = start_time + window_size
            
            # Filter packets in the current window
            window_df = df[(df['time_relative'] >= start_time) & (df['time_relative'] < end_time)]
            
            if not window_df.empty:
                # Basic Stats
                pkt_count = len(window_df)
                byte_count = window_df['length'].sum()
                bytes_per_sec = byte_count / window_size
                
                # Packet Size Stats
                size_mean = window_df['length'].mean()
                size_std = window_df['length'].fillna(0).std() if pkt_count > 1 else 0
                
                # Inter-Arrival Time (IAT) Stats
                if pkt_count > 1:
                    iats = window_df['time_relative'].diff().dropna()
                    iat_mean = iats.mean()
                    iat_std = iats.std()
                else:
                    iat_mean = 0
                    iat_std = 0
                
                # Protocol Distribution
                dns_count = len(window_df[window_df['protocol'].str.contains('DNS', na=False)])
                tls_count = len(window_df[window_df['protocol'].str.contains('TLS|SSL', na=False)])
                quic_count = len(window_df[window_df['protocol'].str.contains('QUIC', na=False)])
                
                tcp_pkts = len(window_df[window_df['proto_id'] == 6])
                udp_pkts = len(window_df[window_df['proto_id'] == 17])
                
                tcp_udp_ratio = tcp_pkts / udp_pkts if udp_pkts > 0 else (tcp_pkts if tcp_pkts > 0 else 0)
                
                # Burst Density (simple heuristic: pkts / window_size)
                burst_density = pkt_count / window_size
                
                # NEW: Temporal Rolling Features (Memory of last 5s)
                prev_bps = [w['bytes_per_sec'] for w in window_history[-5:]] if window_history else [bytes_per_sec]
                rolling_bps_mean = np.mean(prev_bps)
                rolling_bps_std = np.std(prev_bps) if len(prev_bps) > 1 else 0

                # NEW: Jitter (IAT Coefficient of Variation)
                iat_cv = iat_std / (iat_mean + 1e-6)

                # NEW: Payload Density
                payload_ratio = bytes_per_sec / (pkt_count + 1e-6)

                features = {
                    'window_start': start_time,
                    'window_end': end_time,
                    'pkt_count': pkt_count,
                    'byte_count': byte_count,
                    'bytes_per_sec': bytes_per_sec,
                    'rolling_bps_mean': rolling_bps_mean,
                    'rolling_bps_std': rolling_bps_std,
                    'size_mean': size_mean,
                    'size_std': size_std,
                    'iat_mean': iat_mean,
                    'iat_std': iat_std,
                    'iat_cv': iat_cv,
                    'payload_ratio': payload_ratio,
                    'burst_density': burst_density,
                    'dns_count': dns_count,
                    'tls_count': tls_count,
                    'quic_count': quic_count,
                    'tcp_udp_ratio': tcp_udp_ratio
                }
                features_list.append(features)
                window_history.append(features)
            
            start_time += step_size

        features_df = pd.DataFrame(features_list)
        features_df.to_csv(self.output_csv, index=False)
        logger.info(f"Features saved to: {self.output_csv}")
        return features_df

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract statistical features from PCAP")
    parser.add_argument("--pcap", required=True, help="Path to pcapng file")
    parser.add_argument("--window", type=float, default=1.0, help="Window size in seconds")
    parser.add_argument("--step", type=float, default=0.5, help="Step size in seconds")
    
    args = parser.parse_args()
    
    extractor = FeatureExtractor(args.pcap)
    extractor.extract_features(window_size=args.window, step_size=args.step)
