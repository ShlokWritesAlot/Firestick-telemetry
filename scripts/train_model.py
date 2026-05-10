import pandas as pd
import numpy as np
import os
import sys
import pickle
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from datetime import datetime

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import MASTER_DATASET_PATH, MODELS_DIR, LOG_DIR

def train_baseline_models():
    if not os.path.exists(MASTER_DATASET_PATH):
        print(f"Error: Master dataset not found at {MASTER_DATASET_PATH}")
        return

    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # 1. Load Data
    df = pd.read_csv(MASTER_DATASET_PATH)
    
    # Features requested
    features = [
        'pkt_count', 'byte_count', 'bytes_per_sec', 
        'size_mean', 'size_std', 'iat_mean', 'iat_std', 
        'burst_density', 'dns_count', 'tls_count', 
        'quic_count', 'tcp_udp_ratio'
    ]
    
    # Clean data: drop unknown labels for training if needed, but let's keep all for now
    df = df.dropna(subset=features + ['label', 'session_id'])
    
    X = df[features]
    y = df['label']
    groups = df['session_id']

    # 2. SESSION-AWARE SPLIT (Prevent temporal leakage)
    # Entire sessions must be in either train or test, never both.
    gss = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))
    
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    train_sessions = groups.iloc[train_idx].unique()
    test_sessions = groups.iloc[test_idx].unique()

    results_report = []
    results_report.append("="*60)
    results_report.append(f" SCIENTIFIC BASELINE TRAINING REPORT - {datetime.now()}")
    results_report.append("="*60)
    results_report.append(f"Total Rows:     {len(df)}")
    results_report.append(f"Train Sessions: {len(train_sessions)} ({len(X_train)} rows)")
    results_report.append(f"Test Sessions:  {len(test_sessions)} ({len(X_test)} rows)")
    results_report.append("-"*60)
    results_report.append(f"Train IDs: {list(train_sessions)}")
    results_report.append(f"Test IDs:  {list(test_sessions)}")
    results_report.append("-"*60)

    if len(test_sessions) == 0:
        results_report.append("\nWARNING: Too few sessions for a valid split. Testing on training data (NOT SCIENTIFIC).")
        X_test, y_test = X_train, y_train

    # 3. Random Forest
    print("Training RandomForestClassifier...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    
    results_report.append("\n[ RANDOM FOREST - SESSION GENERALIZATION ]")
    results_report.append(f"Accuracy: {accuracy_score(y_test, rf_preds):.4f}")
    results_report.append("\nClassification Report:")
    results_report.append(classification_report(y_test, rf_preds))
    
    # Feature Importance
    importances = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False)
    results_report.append("\nFeature Importance:")
    results_report.append(importances.to_string())

    # 4. Logistic Regression
    print("Training LogisticRegression...")
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    
    results_report.append("\n" + "-"*60)
    results_report.append("\n[ LOGISTIC REGRESSION - SESSION GENERALIZATION ]")
    results_report.append(f"Accuracy: {accuracy_score(y_test, lr_preds):.4f}")
    results_report.append("\nClassification Report:")
    results_report.append(classification_report(y_test, lr_preds))

    # 5. Save Artifacts
    model_path = os.path.join(MODELS_DIR, "workload_classifier_rf.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(rf, f)
    
    # Save Confusion Matrix
    cm = confusion_matrix(y_test, rf_preds)
    cm_df = pd.DataFrame(cm, index=rf.classes_, columns=rf.classes_)
    cm_path = os.path.join(LOG_DIR, "confusion_matrix.csv")
    cm_df.to_csv(cm_path)
    
    report_path = os.path.join(LOG_DIR, "training_report.txt")
    final_report = "\n".join(results_report)
    with open(report_path, "w") as f:
        f.write(final_report)
    
    print(final_report)
    print(f"\nModel saved to: {model_path}")
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    train_baseline_models()
