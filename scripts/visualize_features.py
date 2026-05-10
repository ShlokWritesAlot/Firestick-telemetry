import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import MASTER_DATASET_PATH, PLOTS_DIR

def generate_plots():
    if not os.path.exists(MASTER_DATASET_PATH):
        print(f"Error: Master dataset not found at {MASTER_DATASET_PATH}")
        return

    os.makedirs(PLOTS_DIR, exist_ok=True)
    df = pd.read_csv(MASTER_DATASET_PATH)
    
    # 1. Feature Distribution per Label (Violin-style boxplots)
    print("Generating feature distributions...")
    metrics = ['bytes_per_sec', 'pkt_count', 'quic_count', 'tls_count']
    
    for metric in metrics:
        plt.figure(figsize=(10, 6))
        # Group by label
        data_to_plot = [df[df['label'] == label][metric].dropna() for label in df['label'].unique()]
        labels = df['label'].unique()
        
        plt.boxplot(data_to_plot, labels=labels)
        plt.title(f'Distribution of {metric} per Workload')
        plt.ylabel(metric)
        plt.yscale('log') if df[metric].max() > 1000 else None
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(PLOTS_DIR, f'dist_{metric}.png'))
        plt.close()

    # 2. Time-Series Visualization for a sample session
    if not df.empty:
        sample_session = df['session_id'].unique()[0]
        session_df = df[df['session_id'] == sample_session].sort_values('window_start')
        
        print(f"Generating time-series for session {sample_session}...")
        plt.figure(figsize=(12, 6))
        plt.plot(session_df['window_start'], session_df['bytes_per_sec'], label='Bytes/sec', color='blue')
        plt.twinx()
        plt.plot(session_df['window_start'], session_df['quic_count'], label='QUIC Count', color='red', alpha=0.7)
        plt.title(f'Temporal Features - Session {sample_session}')
        plt.xlabel('Time (s)')
        plt.savefig(os.path.join(PLOTS_DIR, f'timeseries_{sample_session}.png'))
        plt.close()

    # 3. PCA Projection (Visualizing label separation)
    print("Generating PCA projection...")
    features = [
        'pkt_count', 'byte_count', 'bytes_per_sec', 
        'size_mean', 'size_std', 'iat_mean', 'iat_std', 
        'burst_density', 'dns_count', 'tls_count', 
        'quic_count', 'tcp_udp_ratio'
    ]
    
    clean_df = df.dropna(subset=features + ['label'])
    if not clean_df.empty:
        X = clean_df[features]
        y = clean_df['label']
        
        X_scaled = StandardScaler().fit_transform(X)
        pca = PCA(n_components=2)
        components = pca.fit_transform(X_scaled)
        
        plt.figure(figsize=(10, 8))
        for label in y.unique():
            mask = y == label
            plt.scatter(components[mask, 0], components[mask, 1], label=label, alpha=0.6)
            
        plt.title('PCA Projection of Telemetry Features')
        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 2')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(PLOTS_DIR, 'pca_projection.png'))
        plt.close()

    # 4. Correlation Heatmap
    print("Generating correlation matrix...")
    corr = df[features].corr()
    plt.figure(figsize=(12, 10))
    plt.imshow(corr, cmap='coolwarm', interpolation='none')
    plt.colorbar()
    plt.xticks(range(len(features)), features, rotation=90)
    plt.yticks(range(len(features)), features)
    plt.title('Feature Correlation Matrix')
    
    # Annotate numbers
    for i in range(len(features)):
        for j in range(len(features)):
            plt.text(j, i, f'{corr.iloc[i, j]:.2f}', ha='center', va='center', color='white' if abs(corr.iloc[i, j]) > 0.5 else 'black')
            
    plt.savefig(os.path.join(PLOTS_DIR, 'correlation_matrix.png'))
    plt.close()

    print(f"\nAll plots saved to: {PLOTS_DIR}")

if __name__ == "__main__":
    generate_plots()
