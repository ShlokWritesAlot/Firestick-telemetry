import subprocess
import os
import sys
import time
import json
import threading
import pandas as pd
import numpy as np
import pickle
import shap
from datetime import datetime

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import TSHARK_PATH, CAPTURE_INTERFACE, FIRESTICK_MAC, MODELS_DIR

class LiveInferenceEngine:
    def __init__(self, interface=CAPTURE_INTERFACE):
        self.interface = interface
        self.model = None
        self.explainer = None
        self.feature_names = [
            'pkt_count', 'byte_count', 'bytes_per_sec', 
            'size_mean', 'size_std', 'iat_mean', 'iat_std', 
            'burst_density', 'dns_count', 'tls_count', 
            'quic_count', 'tcp_udp_ratio'
        ]
        
        # Buffers
        self.packet_buffer = []
        self.current_stats = {}
        self.is_running = False
        
        self._load_model()

    def _load_model(self):
        model_path = os.path.join(MODELS_DIR, "workload_classifier_rf.pkl")
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            # Initialize SHAP explainer (using a small background sample or just TreeExplainer)
            self.explainer = shap.TreeExplainer(self.model)
            print(f"Loaded model from {model_path}")
        else:
            print(f"WARNING: Model not found at {model_path}. Inference will be simulated.")

    def start(self):
        self.is_running = True
        # Start TShark in a thread
        self.tshark_thread = threading.Thread(target=self._run_tshark, daemon=True)
        self.tshark_thread.start()
        
        # Start Processor in a thread
        self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processor_thread.start()

    def _run_tshark(self):
        """Streams live packet metadata from TShark."""
        # We only need basic fields for real-time stats
        cmd = [
            TSHARK_PATH,
            "-i", str(self.interface),
            "-f", f"ether host {FIRESTICK_MAC} and not tcp port 5555" if FIRESTICK_MAC else "",
            "-T", "fields",
            "-e", "frame.time_epoch",
            "-e", "frame.len",
            "-e", "ip.proto",
            "-e", "tcp.port",
            "-e", "udp.port",
            "-e", "tls.record.content_type",
            "-l" # Line buffered
        ]
        
        print(f"Executing: {' '.join(cmd)}")
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        for line in iter(self.process.stdout.readline, ''):
            if not self.is_running: break
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                try:
                    pkt = {
                        'time': float(parts[0]),
                        'len': int(parts[1]),
                        'proto': parts[2] if len(parts) > 2 else "",
                        'sport': parts[3] if len(parts) > 3 else "",
                        'dport': parts[4] if len(parts) > 4 else "",
                        'tls': parts[5] if len(parts) > 5 else ""
                    }
                    self.packet_buffer.append(pkt)
                except ValueError:
                    continue

    def _process_loop(self):
        """Processes windows of packets every second."""
        while self.is_running:
            time.sleep(1.0)
            if not self.packet_buffer:
                self.current_stats = {"status": "Waiting for traffic..."}
                continue
            
            # Take a 1-second snapshot
            now = time.time()
            snapshot = [p for p in self.packet_buffer if p['time'] > now - 1.0]
            # Keep buffer lean
            self.packet_buffer = [p for p in self.packet_buffer if p['time'] > now - 2.0]
            
            if not snapshot:
                continue
                
            features = self._extract_features(snapshot)
            prediction = self._predict(features)
            
            self.current_stats = {
                "timestamp": datetime.now().isoformat(),
                "metrics": features,
                "prediction": prediction
            }

    def _extract_features(self, pkts):
        lens = [p['len'] for p in pkts]
        times = [p['time'] for p in pkts]
        
        # Basic Stats
        pkt_count = len(pkts)
        byte_count = sum(lens)
        bytes_per_sec = byte_count # 1 second window
        
        size_mean = np.mean(lens) if pkts else 0
        size_std = np.std(lens) if pkts else 0
        
        iats = np.diff(times) if len(times) > 1 else [0]
        iat_mean = np.mean(iats)
        iat_std = np.std(iats)
        
        # Protocol detection (Simplified)
        dns_count = sum(1 for p in pkts if '53' in (p['sport'], p['dport']))
        tls_count = sum(1 for p in pkts if p['tls'] != "")
        quic_count = sum(1 for p in pkts if '443' in (p['sport'], p['dport']) and p['proto'] == '17') # UDP 17
        
        # Burst density (Packets per 100ms max)
        bins = np.histogram(times, bins=10)[0]
        burst_density = np.max(bins) if len(bins) > 0 else 0
        
        is_tcp = sum(1 for p in pkts if p['proto'] == '6')
        is_udp = sum(1 for p in pkts if p['proto'] == '17')
        ratio = is_tcp / (is_udp + 1)
        
        return {
            'pkt_count': pkt_count,
            'byte_count': byte_count,
            'bytes_per_sec': bytes_per_sec,
            'size_mean': size_mean,
            'size_std': size_std,
            'iat_mean': iat_mean,
            'iat_std': iat_std,
            'burst_density': burst_density,
            'dns_count': dns_count,
            'tls_count': tls_count,
            'quic_count': quic_count,
            'tcp_udp_ratio': ratio
        }

    def _predict(self, features_dict):
        if not self.model:
            return {"label": "Model Loading...", "confidence": 0}
            
        X = pd.DataFrame([features_dict])[self.feature_names]
        probs = self.model.predict_proba(X)[0]
        label_idx = np.argmax(probs)
        label = self.model.classes_[label_idx]
        confidence = float(probs[label_idx])
        
        # SHAP Explanations
        shap_values = self.explainer.shap_values(X)
        # Handle multi-class SHAP (list of arrays)
        if isinstance(shap_values, list):
            class_shap = shap_values[label_idx][0]
        else:
            class_shap = shap_values[0] # Single class case
            
        explanations = {
            name: float(val) for name, val in zip(self.feature_names, class_shap)
        }
        
        return {
            "label": label,
            "confidence": confidence,
            "explanations": explanations
        }

    def get_latest_stats(self):
        return self.current_stats

if __name__ == "__main__":
    engine = LiveInferenceEngine()
    engine.start()
    try:
        while True:
            stats = engine.get_latest_stats()
            print(f"\rPrediction: {stats.get('prediction', {}).get('label', 'N/A')} ({stats.get('prediction', {}).get('confidence', 0)*100:.1f}%)", end="")
            time.sleep(0.5)
    except KeyboardInterrupt:
        engine.is_running = False
