# Installation Guide

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11 (required for Windows toast notifications)
- **Python**: 3.8 or higher (3.12 recommended)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Network**: Administrative privileges for packet capture

### Required Software

#### 1. Npcap Installation
Npcap is required for packet capture on Windows.

1. Download Npcap from: https://npcap.com/
2. Run the installer as Administrator
3. **Important**: Enable "Install Npcap in WinPcap API-compatible Mode"
4. Restart your computer after installation

#### 2. Python Dependencies
Install Python dependencies using pip:

```bash
pip install -r requirements.txt
```

#### 3. Optional Dependencies

For enhanced performance:
```bash
pip install numba
```

For plotting and visualization:
```bash
pip install matplotlib seaborn
```

For development:
```bash
pip install pytest pytest-cov black flake8 mypy
```

## Installation Steps

### Option 1: Direct Installation
```bash
# Clone or download the project
cd nids-realtime

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Option 2: Development Installation
```bash
# Clone the repository
git clone <repository-url>
cd nids-realtime

# Create virtual environment (recommended)
python -m venv venv
venv\\Scripts\\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install in development mode
pip install -e .[dev,plotting,performance]
```

## Configuration

### 1. Basic Configuration
Copy and modify the default configuration:
```bash
cp config.yaml my_config.yaml
# Edit my_config.yaml with your settings
```

### 2. Model Setup
If you have MATLAB-trained models:

1. Place your `.mat` files in the `models/` directory
2. Export metadata using the provided script:
   ```bash
   python scripts/export_matlab_metadata.py --mat-file models/your_model.mat
   ```
3. Update `config.yaml` with the correct model paths

For testing without MATLAB models, the system will use a simple heuristic-based model.

### 3. Network Interface
The system will auto-detect your network interface, but you can specify one in `config.yaml`:
```yaml
capture:
  interface: "Ethernet"  # or your interface name
```

To list available interfaces:
```python
from scapy.all import get_if_list
print(get_if_list())
```

## Verification

### 1. Test Installation
```bash
# Run unit tests
pytest tests/

# Test basic functionality
python -c "from nids import RealTimeNIDS; print('Installation successful!')"
```

### 2. Run Demo
```bash
# Synthetic traffic demo
python scripts/demo.py --duration 30

# Or using the main entry point
python main.py --demo --duration 30
```

### 3. Check Network Capture
```bash
# Test packet capture (requires admin privileges)
python -c "
from nids.capture import PacketCapture
capture = PacketCapture()
print(f'Using interface: {capture.interface}')
"
```

## Troubleshooting

### Common Issues

#### 1. "No module named 'scapy'"
```bash
pip install scapy
```

#### 2. "Npcap not found" or packet capture fails
- Ensure Npcap is installed with WinPcap compatibility
- Run Python as Administrator
- Check Windows Firewall settings

#### 3. "Permission denied" for packet capture
- Run command prompt as Administrator
- Ensure your user has network capture privileges

#### 4. Toast notifications not working
- Ensure you're on Windows 10/11
- Check Windows notification settings
- The system will fall back gracefully if notifications fail

#### 5. High CPU usage
- Reduce packet capture rate in config
- Enable Numba optimization
- Adjust feature extraction parameters

### Performance Tuning

#### For High-Traffic Networks
```yaml
performance:
  max_packet_latency: 100  # Increase if needed
  max_concurrent_sessions: 500  # Reduce for lower memory
  use_numba: true
  batch_processing: true
```

#### For Low-Resource Systems
```yaml
features:
  window_size: 5  # Reduce window size
  session_timeout: 60  # Shorter timeout

capture:
  buffer_size: 1024  # Smaller buffer
```

## Next Steps

1. **Configure Models**: Set up your MATLAB-trained models or use the simple model for testing
2. **Customize Features**: Modify feature extraction parameters for your network
3. **Set Alert Thresholds**: Adjust confidence thresholds and alert settings
4. **Test with Real Traffic**: Start with offline PCAP analysis before live deployment

## Support

- Check the README.md for usage examples
- Run `python main.py --help` for command-line options
- Use `pytest tests/` to verify functionality
- Enable verbose logging with `--verbose` for debugging