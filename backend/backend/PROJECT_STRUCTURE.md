# NIDS Backend - Project Structure

## 📁 Directory Organization

```
backend/
├── 🚀 main.py                    # Main entry point
├── 📋 requirements.txt           # Python dependencies
├── ⚙️ setup.py                   # Package setup
├── 📖 README.md                  # Project documentation
├── 🧪 pytest.ini                # Test configuration
│
├── 🌐 api/                       # REST API Server
│   ├── __init__.py
│   └── server.py                 # Flask API endpoints
│
├── ⚙️ config/                    # Configuration Files
│   ├── config.yaml               # Default config (development)
│   ├── development.yaml          # Development settings
│   ├── production.yaml           # Production settings
│   ├── config_http.yaml          # HTTP-only traffic
│   └── config_sensitive.yaml     # Sensitive detection
│
├── 💾 data/                      # Models and Datasets
│   └── models/                   # MATLAB-trained models
│       ├── logistic_regression_model.mat
│       ├── decision_tree_model.mat
│       ├── feature_order.json
│       ├── scaler_params.json
│       └── class_encoder.json
│
├── 📚 docs/                      # Documentation
│   ├── README.md                 # Main documentation
│   ├── INSTALL.md                # Installation guide
│   └── FRONTEND_INTEGRATION.md   # Frontend integration guide
│
├── 🧪 examples/                  # Example Scripts
│   ├── README.md                 # Examples documentation
│   ├── test_nids_detection.py    # Direct NIDS testing
│   ├── test_sensitive_detection.py # Sensitive detection test
│   ├── test_attack_simulation.py # Attack pattern simulation
│   ├── trigger_alerts.py         # Alert trigger scripts
│   ├── debug_features.py         # Feature debugging
│   └── simple_server.py          # Test HTTP server
│
├── 📝 logs/                      # Log Files
│   └── (generated at runtime)
│
├── 🔧 scripts/                   # Utility Scripts
│   ├── demo.py                   # Synthetic demo
│   ├── evaluate_offline.py       # Offline evaluation
│   └── export_matlab_metadata.py # MATLAB model export
│
├── 💻 src/                       # Source Code
│   └── nids/                     # Core NIDS modules
│       ├── __init__.py
│       ├── core.py               # Main NIDS orchestrator
│       ├── capture.py            # Packet capture
│       ├── features.py           # Feature extraction
│       ├── models.py             # Model adapters
│       ├── alerts.py             # Alert management
│       └── schemas.py            # Data structures
│
└── 🧪 tests/                     # Unit Tests
    ├── __init__.py
    ├── test_models.py
    ├── test_features.py
    └── test_alerts.py
```

## 🚀 Quick Start Commands

### Development
```bash
# Start backend with development config
python backend/main.py --config backend/config/development.yaml

# Run demo
python backend/main.py --demo --duration 30

# Start API server
python backend/main.py --api --port 8000
```

### Production
```bash
# Start with production config
python backend/main.py --config backend/config/production.yaml

# Start API server for production
python backend/main.py --api --config backend/config/production.yaml --port 8000
```

### Testing
```bash
# Run unit tests
cd backend && pytest tests/

# Run examples
python backend/examples/test_sensitive_detection.py
python backend/examples/test_attack_simulation.py
```

## 🌐 API Endpoints

The backend provides a REST API for frontend integration:

- **System Control**: `/api/status`, `/api/start`, `/api/stop`
- **Alerts**: `/api/alerts`, `/api/alerts/stream`
- **Statistics**: `/api/stats/history`
- **Demo**: `/api/demo/start`
- **Health**: `/api/health`

## 📊 Features

### ✅ Working Features
- **Real-time packet capture** using Scapy/Npcap
- **Feature extraction** with 66 network flow features
- **Attack detection** using SimpleModelAdapter (heuristic-based)
- **Alert generation** with Windows toast notifications
- **Alert logging** to JSON files
- **REST API** for frontend integration
- **Configuration management** for different environments
- **Synthetic traffic demo** for testing

### 🔄 Ready for Enhancement
- **MATLAB model integration** (structure ready, needs implementation)
- **WebSocket support** for real-time frontend updates
- **Database integration** for persistent storage
- **Advanced visualization** endpoints
- **User authentication** and authorization

## 🎯 Frontend Integration

The backend is designed to work with any frontend framework:

- **React/Vue/Angular**: Use the REST API endpoints
- **Real-time updates**: Server-Sent Events (SSE) for live alerts
- **CORS support**: Configurable for development/production
- **JSON responses**: Standard format for easy parsing

See `docs/FRONTEND_INTEGRATION.md` for detailed integration guide.

## 🔧 Configuration

### Environment-Specific Configs
- **development.yaml**: Lower thresholds, more logging, CORS enabled
- **production.yaml**: Higher thresholds, minimal logging, security focused
- **config_sensitive.yaml**: Very sensitive detection for testing
- **config_http.yaml**: HTTP/HTTPS traffic only

### Key Configuration Sections
- **models**: Model paths and thresholds
- **capture**: Network interface and filtering
- **features**: Feature extraction parameters
- **alerts**: Notification and logging settings
- **api**: REST API configuration

## 📈 Performance

### Current Capabilities
- **Throughput**: 100+ packets/second
- **Latency**: <50ms average processing time
- **Memory**: Configurable session limits
- **Alerts**: Real-time generation and logging

### Scalability
- Multi-threaded processing
- Configurable buffer sizes
- Session timeout management
- Alert cooldown mechanisms

## 🛡️ Security

### Current Security Features
- Configurable alert thresholds
- Attack type classification
- Confidence scoring
- Comprehensive logging

### Production Considerations
- Run with appropriate network privileges
- Configure firewall rules
- Secure API endpoints
- Monitor log files

## 📝 Next Steps

1. **Frontend Development**: Build dashboard using the API
2. **MATLAB Integration**: Complete model loading implementation
3. **Database Integration**: Add persistent storage
4. **Advanced Features**: WebSockets, user management
5. **Deployment**: Docker containers, cloud deployment

This backend provides a solid foundation for a complete Network Intrusion Detection System with modern architecture and frontend-ready APIs!