# Real-Time Network Intrusion Detection System

A modular Python pipeline for real-time network intrusion detection using MATLAB-trained models.

## Features

- **Real-time packet capture** using Scapy + Npcap
- **Modular architecture** with swappable components
- **MATLAB model compatibility** for logistic regression and multi-class classification
- **Low-latency processing** (≤50ms per packet, ≤200ms for multi-class)
- **Windows toast notifications** for alerts
- **Comprehensive evaluation** with precision/recall/F1 metrics

## Architecture

```
Capture → Parse → Sessionize → Features → Scale/Encode → Select → Model → Alert
```

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

**Quick Start:**
1. Install Npcap from https://npcap.com/ (with WinPcap compatibility)
2. `pip install -r requirements.txt`
3. `python scripts/export_matlab_metadata.py --create-sample` (for testing)
4. `python main.py --demo` (run demo)

## Quick Start

```python
from nids import RealTimeNIDS

# Initialize system
nids = RealTimeNIDS('config.yaml')

# Start real-time detection
nids.start_detection()
```

## Configuration

Edit `config.yaml` to customize:
- Model paths and thresholds
- Feature extraction parameters
- Alert settings
- Performance tuning options

## Latency Targets

- **Per-packet binary inference**: ≤50ms average
- **Multi-class classification**: +200ms when triggered
- **Memory usage**: Optimized for single-core laptops

## Testing

```bash
# Run unit tests
pytest tests/

# Evaluate on PCAP replay
python scripts/evaluate_offline.py --pcap sample.pcap --config config.yaml
```