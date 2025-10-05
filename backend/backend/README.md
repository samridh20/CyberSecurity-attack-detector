# NIDS Backend

Real-Time Network Intrusion Detection System Backend

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd backend

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Basic Usage

```bash
# Start real-time detection
python main.py

# Start with custom config
python main.py --config config/production.yaml

# Run demo
python main.py --demo --duration 60

# Start API server
python main.py --api --port 8000
```

## 📁 Directory Structure

```
backend/
├── src/nids/           # Core NIDS modules
├── api/                # REST API server
├── config/             # Configuration files
├── data/               # Models and datasets
├── scripts/            # Utility scripts
├── tests/              # Unit tests
├── examples/           # Example scripts
├── docs/               # Documentation
├── logs/               # Log files
└── main.py             # Main entry point
```

## 🔧 Configuration

### Development
```bash
python main.py --config config/development.yaml
```

### Production
```bash
python main.py --config config/production.yaml
```

## 🌐 API Endpoints

### System Control
- `GET /api/status` - Get system status
- `POST /api/start` - Start detection
- `POST /api/stop` - Stop detection
- `GET /api/health` - Health check

### Alerts
- `GET /api/alerts` - Get recent alerts
- `GET /api/alerts/stream` - Stream alerts (SSE)

### Statistics
- `GET /api/stats/history` - Get historical stats

### Demo
- `POST /api/demo/start` - Start synthetic demo

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/nids

# Run specific test
pytest tests/test_models.py
```

## 📊 Examples

### Basic Detection
```python
from nids import RealTimeNIDS

# Initialize NIDS
nids = RealTimeNIDS("config/config.yaml")

# Start detection
nids.start_detection()

# Get status
status = nids.get_status()
print(f"Processed: {status['packets_processed']} packets")
```

### API Integration
```python
import requests

# Start detection via API
response = requests.post("http://localhost:8000/api/start")

# Get alerts
alerts = requests.get("http://localhost:8000/api/alerts").json()
```

## 🔒 Security Features

- Real-time packet analysis
- Machine learning-based detection
- Multiple attack type classification
- Configurable alert thresholds
- Windows toast notifications
- Comprehensive logging

## 📈 Performance

- **Throughput**: 1000+ packets/second
- **Latency**: <50ms average processing time
- **Memory**: Configurable session limits
- **Scalability**: Multi-threaded processing

## 🛠️ Development

### Code Style
```bash
# Format code
black src/ api/ tests/

# Lint code
flake8 src/ api/ tests/

# Type checking
mypy src/ api/
```

### Adding New Features
1. Create feature branch
2. Add tests in `tests/`
3. Update documentation
4. Submit pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📞 Support

- Documentation: `docs/`
- Issues: GitHub Issues
- Email: team@nids.local