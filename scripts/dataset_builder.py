import os
import pandas as pd
import numpy as np
import sys
import glob

# Add parent directory to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import FEATURE_DIR, LABEL_DIR, LOG_DIR, DATASET_DIR, MASTER_DATASET_PATH
from scripts.utils import setup_logging

logger = setup_logging("DatasetBuilder")

class DatasetBuilder:
    def __init__(self):
        os.makedirs(DATASET_DIR, exist_ok=True)
        self.report_path = os.path.join(LOG_DIR, "master_dataset_report.txt")
        
        # QUALITY THRESHOLDS
        self.min_duration = 5.0  # seconds
        self.min_packets = 50     # per session

    def _get_active_label_and_app(self, window_end_relative, label_df, session_start_unix):
        """Finds the most recent label and app active at the end of a feature window."""
        if 'relative_time' not in label_df.columns:
            label_df['relative_time'] = label_df['timestamp_unix'] - session_start_unix
        
        past_labels = label_df[label_df['relative_time'] <= window_end_relative]
        if past_labels.empty:
            return "unknown", "unknown"
        
        latest = past_labels.iloc[-1]
        return latest['label'], latest['app']

    def build_dataset(self):
        feature_files = glob.glob(os.path.join(FEATURE_DIR, "session_*_features.csv"))
        all_frames = []
        stats = {
            "total_sessions": 0,
            "rejected_quality": 0,
            "rejected_missing": 0,
            "total_rows": 0,
            "label_distribution": {},
            "app_distribution": {}
        }

        logger.info(f"Scanning {len(feature_files)} sessions for master dataset...")

        for f_path in feature_files:
            # Handle both session_ID_features.csv formats
            parts = os.path.basename(f_path).split('_')
            session_id = f"{parts[1]}_{parts[2]}"
            
            l_path = os.path.join(LABEL_DIR, f"session_{session_id}_labels.csv")
            v_path = os.path.join(LOG_DIR, f"session_{session_id}_capture_report.txt")

            if not os.path.exists(l_path):
                logger.warning(f"Session {session_id}: Labels missing. Skipping.")
                stats["rejected_missing"] += 1
                continue

            # Load Data
            f_df = pd.read_csv(f_path)
            l_df = pd.read_csv(l_path)
            
            if f_df.empty or l_df.empty:
                logger.warning(f"Session {session_id}: Empty data files. Skipping.")
                stats["rejected_quality"] += 1
                continue

            # 1. Quality Filter: Duration
            duration = f_df['window_end'].max()
            if duration < self.min_duration:
                logger.warning(f"Session {session_id}: Duration {duration:.1f}s too short (<{self.min_duration}s). Rejecting.")
                stats["rejected_quality"] += 1
                continue

            # 2. Quality Filter: Packet Count
            total_packets = f_df['pkt_count'].sum()
            if total_packets < self.min_packets:
                logger.warning(f"Session {session_id}: Packet count {total_packets} too low (<{self.min_packets}). Rejecting.")
                stats["rejected_quality"] += 1
                continue

            # 3. Quality Check: Validation Report
            if os.path.exists(v_path):
                with open(v_path, 'r') as v_file:
                    content = v_file.read()
                    if "EMPTY_CAPTURE" in content:
                        logger.warning(f"Session {session_id}: Empty capture report. Rejecting.")
                        stats["rejected_quality"] += 1
                        continue
            
            # Use the first label's timestamp as the session start reference
            session_start_unix = l_df.iloc[0]['timestamp_unix']
            
            # Merge logic: Add label and app to each window
            labels_apps = f_df['window_end'].apply(
                lambda x: self._get_active_label_and_app(x, l_df, session_start_unix)
            )
            f_df['label'] = [la[0] for la in labels_apps]
            f_df['app'] = [la[1] for la in labels_apps]
            
            f_df['session_id'] = session_id
            all_frames.append(f_df)
            stats["total_sessions"] += 1

        if not all_frames:
            logger.error("No valid sessions found to build dataset.")
            return

        master_df = pd.concat(all_frames, ignore_index=True)
        
        # Clean: Remove duplicates and "unknown" labels if they dominate
        initial_len = len(master_df)
        master_df.drop_duplicates(subset=['session_id', 'window_start', 'window_end'], inplace=True)
        stats["duplicates_removed"] = initial_len - len(master_df)

        # Save Master
        master_df.to_csv(MASTER_DATASET_PATH, index=False)
        stats["total_rows"] = len(master_df)
        stats["label_distribution"] = master_df['label'].value_counts().to_dict()
        stats["app_distribution"] = master_df['app'].value_counts().to_dict()

        self._generate_report(stats)
        logger.info(f"Master dataset updated: {MASTER_DATASET_PATH}")
        return master_df

    def _generate_report(self, stats):
        report = [
            "="*50,
            " MASTER DATASET QUALITY REPORT",
            "="*50,
            f"Valid Sessions:    {stats['total_sessions']}",
            f"Rejected (Quality): {stats['rejected_quality']}",
            f"Rejected (Missing): {stats['rejected_missing']}",
            f"Total Data Rows:   {stats['total_rows']}",
            f"Duplicates Removed: {stats['duplicates_removed']}",
            "-"*50,
            "LABEL DISTRIBUTION:",
        ]
        for label, count in stats["label_distribution"].items():
            report.append(f"  {label:<15} : {count} ({count/stats['total_rows']*100:.1f}%)")
        
        report.append("-"*50)
        report.append("APP DISTRIBUTION:")
        for app, count in stats["app_distribution"].items():
            report.append(f"  {app:<15} : {count}")
            
        report.append("="*50)
        
        with open(self.report_path, "w") as f:
            f.write("\n".join(report))
        print("\n".join(report))

if __name__ == "__main__":
    builder = DatasetBuilder()
    builder.build_dataset()
