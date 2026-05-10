from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np
import os
import sys
import pickle
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from datetime import datetime

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import MASTER_DATASET_PATH, MODELS_DIR, LOG_DIR

def load_and_clean_data(csv_path):
    if not os.path.exists(csv_path): return None
    df = pd.read_csv(csv_path)
    
    # TRANSITION SCRUBBING (Preserving more data)
    clean_dfs = []
    for sid in df['session_id'].unique():
        s_df = df[df['session_id'] == sid].sort_values('window_start')
        # Scrub only 2s from start/end to keep more signal
        start_cut = s_df['window_start'].min() + 2.0
        end_cut = s_df['window_start'].max() - 2.0
        stable_df = s_df[(s_df['window_start'] >= start_cut) & (s_df['window_start'] <= end_cut)]
        if len(stable_df) > 2:
            clean_dfs.append(stable_df)
    
    return pd.concat(clean_dfs) if clean_dfs else df

def train_baseline_models():
    if not os.path.exists(MASTER_DATASET_PATH): return
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    df = load_and_clean_data(MASTER_DATASET_PATH)
    
    features = [
        'pkt_count', 'byte_count', 'bytes_per_sec', 
        'rolling_bps_mean', 'rolling_bps_std',
        'size_mean', 'size_std', 'iat_mean', 'iat_std', 
        'iat_cv', 'payload_ratio', 'burst_density',
        'dns_count', 'tls_count', 'quic_count', 'tcp_udp_ratio'
    ]
    
    df = df.dropna(subset=features + ['label', 'session_id'])
    # Filter out 'unknown' labels for cleaner training
    df = df[df['label'] != 'unknown']
    
    X = df[features]
    y = df['label']
    groups = df['session_id']

    gss = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    print(f"Training on {len(X_train)} samples from {len(groups.iloc[train_idx].unique())} sessions...")

    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    
    report = []
    report.append(f"ACCURACY: {accuracy_score(y_test, preds):.4f}")
    report.append("\n" + classification_report(y_test, preds))
    
    # Feature Importance
    importances = pd.Series(clf.feature_importances_, index=features).sort_values(ascending=False)
    report.append("\nTOP FEATURES:\n" + importances.head(5).to_string())
    
    final_report = "\n".join(report)
    print(final_report)
    
    with open(os.path.join(MODELS_DIR, "workload_classifier_rf.pkl"), 'wb') as f:
        pickle.dump(clf, f)
    with open(os.path.join(LOG_DIR, "training_report.txt"), 'w') as f:
        f.write(final_report)

if __name__ == "__main__":
    train_baseline_models()
