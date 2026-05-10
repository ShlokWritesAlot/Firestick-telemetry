# EdgePulse FireStick Telemetry Node

## Overview
EdgePulse FireStick Telemetry Node is a specialized framework designed for remotely controlling Amazon Fire TV Sticks and generating precise, timestamped workload labels. This data serves as the foundation for future encrypted traffic analysis and network performance experiments.

## Project Structure
- `scripts/`: Core Python logic for ADB control and utilities.
- `captures/`: Storage for screenshots and visual data.
- `labels/`: Timestamped workload labels (CSV/JSON).
- `data/`: Raw telemetry or workload data.
- `docs/`: Technical documentation and research notes.
- `notebooks/`: Exploratory Data Analysis (EDA) and visualization.
- `logs/`: Application execution logs.

## Setup
1. **Prerequisites**: 
   - Python 3.8+
   - ADB (Android Debug Bridge) installed and added to PATH.
   - Fire TV Stick with "ADB Debugging" enabled in Developer Options.

2. **Installation**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**:
   Update `scripts/config.py` or create a `.env` file with your FireStick's IP address.

## Usage
Run the main controller script to start capturing workload labels:
```bash
python scripts/adb_controller.py
```

## Features
- **Remote Control**: Mapping of standard Fire TV remote keys (HOME, BACK, etc.).
- **App Management**: Launch apps via package names.
- **State Monitoring**: Query foreground activity for real-time workload labeling.
- **Robust Logging**: Detailed execution logs with high-precision timestamps.
