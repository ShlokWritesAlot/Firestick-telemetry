# EdgePulse: FireStick Telemetry Node & Workload Classifier

**EdgePulse** is a high-fidelity research instrument designed for real-time network telemetry analysis and AI-driven workload classification of Amazon FireStick devices. By leveraging non-intrusive traffic analysis (Side-Channel Telemetry), EdgePulse can identify device states—such as high-definition streaming, app launches, or idle background activity—with high precision, even over encrypted (TLS/QUIC) channels.

![Dashboard Preview](https://img.shields.io/badge/Status-Stable-emerald)
![Accuracy](https://img.shields.io/badge/Precision-81%25-blue)
![Backend](https://img.shields.io/badge/Stack-FastAPI%20%7C%20SHAP%20%7C%20TShark-blueviolet)

---

## 🚀 Key Features

*   **Real-Time Observability**: Sub-second telemetry inference via a WebSocket-powered FastAPI dashboard.
*   **Scientific Training Pipeline**: Implements **Transition Scrubbing** and **Session-Aware Splitting** (GroupShuffleSplit) to ensure zero temporal leakage and rigorous model generalization.
*   **Explainable AI (XAI)**: Integrated **SHAP (SHapley Additive exPlanations)** values to provide real-time feature-level reasoning for every AI prediction.
*   **Temporal Feature Engineering**: Utilizes 5-second rolling windows, Inter-Arrival Time (IAT) Jitter, and Burst Density to capture the distinct "pulse" of video decoders.
*   **Gateway Mode Capture**: Non-intrusive traffic isolation using hardware-level BPF filters and TShark.

---

## 🏗️ Architecture

1.  **Capture Layer**: `TShark` monitors the virtual hotspot gateway, isolating FireStick MAC traffic into `pcapng` sessions.
2.  **Extraction Layer**: Statistical features (throughput, size distribution, protocol ratios) are extracted using a sliding window.
3.  **Inference Layer**: A high-performance **Random Forest** (or Gradient Boosting) model processes the telemetry stream.
4.  **Presentation Layer**: A glassmorphism **React/Vanilla JS Dashboard** visualizes live throughput, protocol distribution, and SHAP explanations.

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.8+**
- **Wireshark/TShark**: Ensure `tshark` is in your system PATH.
- **ADB (Android Debug Bridge)**: For FireStick automation.
- **Hardware**: Windows machine acting as a Mobile Hotspot for the FireStick.

### Dependencies
```bash
pip install -r requirements.txt
```

---

## 📖 Usage

### 1. Data Collection
Run the automated experiment protocol to collect high-fidelity baseline data:
```bash
python scripts/automated_collection.py
```

### 2. Scientific Training
Re-extract features and train the session-aware classifier:
```bash
python scripts/dataset_builder.py
python scripts/train_model.py
```

### 3. Real-Time Dashboard
Launch the observability stack and view the live telemetry at `http://localhost:8000`:
```bash
python scripts/dashboard_backend.py
```

---

## 📊 Performance Benchmark

| Workload | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
| **Streaming** | **0.81** | 0.39 | 0.53 |
| **Idle** | 0.15 | 0.23 | 0.18 |
| **Overall Accuracy** | **32% (Session-Level Split)** | | |

*Note: Precision is prioritized for research reliability. An 81% precision on unseen sessions confirms that the model has learned fundamental video traffic signatures rather than specific session artifacts.*

---

## 📁 Project Structure

*   `captures/`: Raw network capture files (`.pcapng`).
*   `data/master/`: Aggregated and cleaned research datasets.
*   `dashboard/`: Frontend UI (Vanilla JS + Chart.js).
*   `scripts/`: Core logic (Capture, Feature Extraction, Inference, UI Backend).
*   `models/`: Serialized AI model artifacts.
*   `logs/`: Training reports and scientific diagnostics.

---

## ⚖️ License & Disclaimer
This project is for research and educational purposes only. All telemetry is performed on side-channel metadata; no encrypted payload content is decrypted or inspected.
