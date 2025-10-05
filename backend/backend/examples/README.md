# NIDS Backend Examples

This directory contains example scripts and demonstrations for the NIDS Backend.

## 📁 Files

### Core Examples
- `test_nids_detection.py` - Direct NIDS testing with synthetic packets
- `test_sensitive_detection.py` - Sensitive detection configuration testing
- `debug_features.py` - Feature extraction debugging

### Attack Simulation
- `test_attack_simulation.py` - Safe attack pattern simulation
- `trigger_alerts.py` - Scripts to trigger specific alert types

### Utilities
- `simple_server.py` - Simple HTTP server for testing

## 🚀 Usage Examples

### 1. Basic Detection Test
```bash
cd backend
python examples/test_nids_detection.py
```

### 2. Sensitive Detection
```bash
python examples/test_sensitive_detection.py
```

### 3. Attack Simulation
```bash
# Start simple server in one terminal
python examples/simple_server.py

# Run attack simulation in another terminal
python examples/test_attack_simulation.py --attack-type all
```

### 4. Feature Debugging
```bash
python examples/debug_features.py
```

## 🔧 Configuration

Most examples use the configuration files in `../config/`:
- `development.yaml` - Development settings (more sensitive)
- `production.yaml` - Production settings (less sensitive)
- `config.yaml` - Default configuration

## 📊 Expected Output

### Detection Test
```
=== Direct NIDS Attack Detection Test ===
Testing dos attack...
  🚨 ATTACK DETECTED!
     Confidence: 0.536
     Attack Type: DoS
     Source: 192.168.1.200:12345

Total alerts generated: 47
```

### Attack Simulation
```
=== NIDS Attack Simulation ===
1. DoS Flood Simulation
Starting DoS simulation: 10 threads for 15 seconds
Thread completed: 150 connection attempts

2. Port Scan Simulation
Starting port scan simulation: ports 20-100
Port scan completed. Found 1 open ports: [8080]
```

## 🧪 Testing Integration

These examples are designed to work with:
- Real-time NIDS detection
- API server endpoints
- Frontend dashboard integration

## 📝 Notes

- Examples use localhost/loopback for safety
- No external systems are affected
- All traffic is synthetic or local
- Windows toast notifications may appear during testing