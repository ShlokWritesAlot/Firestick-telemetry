import pandas as pd
import os
import sys

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import MASTER_DATASET_PATH, LOG_DIR

def analyze_dataset():
    if not os.path.exists(MASTER_DATASET_PATH):
        print(f"Error: Master dataset not found at {MASTER_DATASET_PATH}")
        return

    df = pd.read_csv(MASTER_DATASET_PATH)
    
    report = []
    report.append("="*50)
    report.append(" BASELINE DATASET ANALYSIS")
    report.append("="*50)
    
    # 1. Label Counts
    report.append("\n[ 1. LABEL COUNTS ]")
    counts = df['label'].value_counts()
    report.append(counts.to_string())
    
    # 2. Key Averages per Label
    report.append("\n\n[ 2. STATISTICAL AVERAGES PER LABEL ]")
    metrics = [
        'bytes_per_sec', 'quic_count', 'tls_count', 
        'burst_density', 'pkt_count', 'size_mean'
    ]
    
    analysis = df.groupby('label')[metrics].mean()
    report.append(analysis.to_string())
    
    # 3. Protocol Ratios
    report.append("\n\n[ 3. PROTOCOL RATIOS ]")
    # TCP vs UDP (Proto ID 6 vs 17 heuristic)
    df['is_tcp'] = df['tcp_udp_ratio'] > 0 # Simple check
    
    # 4. Top Distinguishing Features (Standard Deviation across means)
    report.append("\n\n[ 4. FEATURE VARIANCE ACROSS LABELS ]")
    # Which features have the most variance between label means?
    label_means = df.groupby('label').mean(numeric_only=True)
    # Normalize means to compare variance
    normalized_means = (label_means - label_means.min()) / (label_means.max() - label_means.min())
    variances = normalized_means.std().sort_values(ascending=False)
    report.append("Top features distinguishing labels (by variance of means):")
    report.append(variances.head(10).to_string())

    final_report = "\n".join(report)
    
    analysis_path = os.path.join(LOG_DIR, "dataset_analysis.txt")
    with open(analysis_path, "w") as f:
        f.write(final_report)
    
    print(final_report)
    print(f"\nAnalysis saved to: {analysis_path}")

if __name__ == "__main__":
    analyze_dataset()
