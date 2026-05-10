import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import MASTER_DATASET_PATH, LOG_DIR

def analyze_sessions():
    if not os.path.exists(MASTER_DATASET_PATH):
        print(f"Error: Master dataset not found at {MASTER_DATASET_PATH}")
        return

    df = pd.read_csv(MASTER_DATASET_PATH)
    
    report = []
    report.append("="*60)
    report.append(" ADVANCED SESSION-LEVEL ANALYSIS REPORT")
    report.append("="*60)
    
    # 1. Per-Session Statistics
    report.append("\n[ 1. PER-SESSION TELEMETRY SUMMARY ]")
    session_stats = df.groupby('session_id').agg({
        'pkt_count': 'sum',
        'bytes_per_sec': 'mean',
        'quic_count': 'sum',
        'tls_count': 'sum',
        'window_end': 'max'
    }).rename(columns={'window_end': 'duration_s'})
    
    report.append(session_stats.to_string())
    
    # 2. Per-Label Detailed Analysis
    report.append("\n\n[ 2. PER-LABEL FEATURE DISTRIBUTIONS ]")
    metrics = ['bytes_per_sec', 'quic_count', 'tls_count', 'iat_std', 'size_mean']
    label_stats = df.groupby('label')[metrics].agg(['mean', 'std'])
    report.append(label_stats.to_string())
    
    # 3. Label Overlap Detection
    # If different labels have very similar feature means, they might be hard to distinguish
    report.append("\n\n[ 3. LABEL OVERLAP & CONFUSION VULNERABILITY ]")
    label_means = df.groupby('label')[metrics].mean()
    # Normalize to compare
    norm_means = (label_means - label_means.min()) / (label_means.max() - label_means.min())
    
    for i, label1 in enumerate(norm_means.index):
        for j, label2 in enumerate(norm_means.index):
            if i < j:
                dist = np.linalg.norm(norm_means.loc[label1] - norm_means.loc[label2])
                if dist < 0.2:
                    report.append(f"WARNING: High Overlap detected between '{label1}' and '{label2}' (Dist: {dist:.4f})")
    
    # 4. Low-Information Session Detection
    report.append("\n\n[ 4. DATA QUALITY ALERTS ]")
    for session_id, row in session_stats.iterrows():
        if row['pkt_count'] < 100:
            report.append(f"ALERT: Session {session_id} has very low packet activity ({row['pkt_count']} pkts).")
        if row['quic_count'] == 0 and df[df['session_id'] == session_id]['label'].iloc[0] == 'streaming':
            report.append(f"ALERT: Streaming session {session_id} has ZERO QUIC traffic. Check Hotspot setup.")

    final_report = "\n".join(report)
    
    output_path = os.path.join(LOG_DIR, "session_analysis_report.txt")
    with open(output_path, "w") as f:
        f.write(final_report)
    
    print(final_report)
    print(f"\nAdvanced analysis saved to: {output_path}")

if __name__ == "__main__":
    analyze_sessions()
