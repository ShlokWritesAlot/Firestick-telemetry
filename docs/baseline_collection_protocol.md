# EdgePulse Baseline Telemetry Collection Protocol (v2.0 - Gold Standard)

This document outlines the standard operating procedure for collecting high-quality, scientifically valid telemetry data.

## 1. The Golden Rule: "No Interaction Cooldown"
**Wait 5 seconds** before and after each labeled event. 
*   Why? This prevents "label contamination" where App Launch traffic bleeds into Streaming traffic, causing model confusion.

## 2. Target Distribution & Resolution Diversity

To ensure generalization across Adaptive Bitrate (ABR) behaviors, vary resolutions:

| Workload | Target | Description |
| :--- | :--- | :--- |
| **IDLE** | 15 | Device on Home screen, no interaction. |
| **APP_LAUNCH** | 15 | YouTube/Netflix/Prime launch (Wait 10s cooldown). |
| **STREAMING (480p)** | 10 | Low resolution (Stable bitrate). |
| **STREAMING (720p)** | 10 | Medium resolution. |
| **STREAMING (1080p)** | 10 | High resolution (Bursty behavior). |
| **PAUSED_STREAM** | 10 | Active stream that is currently paused. |
| **TRUE_BUFFERING** | 10 | Real network degradation (Throttled hotspot). |
| **PAUSE_RESUME** | 10 | User-triggered pause (for comparison). |

## 3. Collection Rules

### IDLE vs. PAUSED_STREAM
- **IDLE**: No app is active (Home Screen).
- **PAUSED_STREAM**: A video is loaded but paused. Keep-alives and metadata refreshes are the key signals here.

### Resolution Diversity
- Manually set the resolution in the YouTube/Prime app settings before starting the label.
- Record the resolution in the session metadata.

### Buffering Distinction
- Do **not** use the "Pause" button to simulate "True Buffering."
- To simulate **True Buffering**: Briefly disable the internet on the laptop or use a bandwidth limiter on the Hotspot interface.

## 4. Metadata Requirements
Every session must include the following in the notes:
- `wifi_strength`: (Excellent/Good/Fair/Poor)
- `resolution`: (480p/720p/1080p/Auto)
- `app`: (YouTube/Netflix/Prime)
- `network_type`: (Home_WiFi/Hotspot)

## 5. Quality Control Checklist
- [x] Wait 5s before labeling.
- [x] Verify resolution is locked.
- [x] Check for "Empty Capture" warnings.
- [x] Ensure `session_analysis_report.txt` shows valid QUIC for streaming.
