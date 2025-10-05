# Frontend Integration Guide

This guide explains how to integrate a frontend application with the NIDS Backend API.

## 🌐 API Overview

The NIDS Backend provides a REST API with real-time capabilities for frontend integration.

### Base URL
```
http://localhost:8000/api
```

## 🔌 API Endpoints

### System Control

#### Get System Status
```http
GET /api/status
```

**Response:**
```json
{
  "running": true,
  "uptime_seconds": 3600.5,
  "packets_processed": 15420,
  "alerts_generated": 23,
  "active_flows": 156,
  "packets_per_second": 4.3,
  "avg_latency_ms": 12.5
}
```

#### Start Detection
```http
POST /api/start
```

**Response:**
```json
{
  "message": "NIDS detection started"
}
```

#### Stop Detection
```http
POST /api/stop
```

**Response:**
```json
{
  "message": "NIDS detection stopped"
}
```

### Alerts

#### Get Recent Alerts
```http
GET /api/alerts?limit=50&offset=0
```

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-123",
      "timestamp": 1759636847.4157968,
      "severity": "high",
      "description": "DoS attack detected from 192.168.1.200",
      "source_ip": "192.168.1.200",
      "destination_ip": "10.0.0.100",
      "attack_type": "DoS",
      "confidence": 0.856
    }
  ],
  "total": 23,
  "limit": 50,
  "offset": 0
}
```

#### Stream Alerts (Server-Sent Events)
```http
GET /api/alerts/stream
```

**Response:** (SSE Stream)
```
data: {"id": "alert-124", "timestamp": 1759636850.1, "severity": "medium", ...}

data: {"id": "alert-125", "timestamp": 1759636852.3, "severity": "low", ...}
```

### Statistics

#### Get Historical Statistics
```http
GET /api/stats/history?hours=24
```

**Response:**
```json
{
  "stats": [
    {
      "timestamp": 1759636800.0,
      "packets_processed": 15000,
      "alerts_generated": 20,
      "packets_per_second": 4.2
    }
  ],
  "hours": 24
}
```

### Demo

#### Start Synthetic Demo
```http
POST /api/demo/start
Content-Type: application/json

{
  "duration": 60
}
```

**Response:**
```json
{
  "message": "Demo started for 60 seconds"
}
```

## 🔄 Real-Time Integration

### Server-Sent Events (SSE)
For real-time alerts, use Server-Sent Events:

```javascript
const eventSource = new EventSource('http://localhost:8000/api/alerts/stream');

eventSource.onmessage = function(event) {
  const alert = JSON.parse(event.data);
  console.log('New alert:', alert);
  
  // Update UI with new alert
  displayAlert(alert);
};

eventSource.onerror = function(event) {
  console.error('SSE error:', event);
};
```

### WebSocket Alternative
For more complex real-time features, consider implementing WebSocket support.

## 📊 Frontend Components

### Dashboard Components

#### System Status Widget
```javascript
async function updateSystemStatus() {
  const response = await fetch('/api/status');
  const status = await response.json();
  
  document.getElementById('packets-processed').textContent = status.packets_processed;
  document.getElementById('alerts-count').textContent = status.alerts_generated;
  document.getElementById('pps').textContent = status.packets_per_second.toFixed(1);
}

// Update every 5 seconds
setInterval(updateSystemStatus, 5000);
```

#### Alerts List
```javascript
async function loadAlerts(limit = 50, offset = 0) {
  const response = await fetch(`/api/alerts?limit=${limit}&offset=${offset}`);
  const data = await response.json();
  
  const alertsList = document.getElementById('alerts-list');
  alertsList.innerHTML = '';
  
  data.alerts.forEach(alert => {
    const alertElement = createAlertElement(alert);
    alertsList.appendChild(alertElement);
  });
}

function createAlertElement(alert) {
  const div = document.createElement('div');
  div.className = `alert alert-${alert.severity}`;
  div.innerHTML = `
    <div class="alert-header">
      <span class="severity">${alert.severity.toUpperCase()}</span>
      <span class="timestamp">${new Date(alert.timestamp * 1000).toLocaleString()}</span>
    </div>
    <div class="alert-body">
      <p>${alert.description}</p>
      <p>Source: ${alert.source_ip} → ${alert.destination_ip}</p>
      <p>Confidence: ${(alert.confidence * 100).toFixed(1)}%</p>
    </div>
  `;
  return div;
}
```

#### Control Panel
```javascript
async function startDetection() {
  try {
    const response = await fetch('/api/start', { method: 'POST' });
    const result = await response.json();
    
    if (response.ok) {
      showNotification('Detection started', 'success');
      updateControlButtons(true);
    } else {
      showNotification(result.error, 'error');
    }
  } catch (error) {
    showNotification('Failed to start detection', 'error');
  }
}

async function stopDetection() {
  try {
    const response = await fetch('/api/stop', { method: 'POST' });
    const result = await response.json();
    
    if (response.ok) {
      showNotification('Detection stopped', 'success');
      updateControlButtons(false);
    } else {
      showNotification(result.error, 'error');
    }
  } catch (error) {
    showNotification('Failed to stop detection', 'error');
  }
}
```

### Charts and Visualization

#### Real-Time Statistics Chart
```javascript
// Using Chart.js or similar library
const ctx = document.getElementById('stats-chart').getContext('2d');
const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Packets/Second',
      data: [],
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1
    }]
  },
  options: {
    responsive: true,
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'minute'
        }
      }
    }
  }
});

// Update chart with new data
function updateChart(timestamp, packetsPerSecond) {
  chart.data.labels.push(new Date(timestamp * 1000));
  chart.data.datasets[0].data.push(packetsPerSecond);
  
  // Keep only last 100 points
  if (chart.data.labels.length > 100) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  
  chart.update('none');
}
```

## 🎨 UI/UX Recommendations

### Color Coding
- **Green**: Normal operation, low severity alerts
- **Yellow**: Medium severity alerts, warnings
- **Red**: High severity alerts, critical issues
- **Blue**: System information, statistics

### Alert Severity Levels
- **Low**: Suspicious activity, potential false positives
- **Medium**: Likely attacks, requires attention
- **High**: Confirmed attacks, immediate action required
- **Critical**: System compromise, emergency response

### Responsive Design
- Mobile-friendly alert notifications
- Collapsible sidebar for navigation
- Responsive charts and tables
- Touch-friendly controls

## 🔒 Security Considerations

### CORS Configuration
The backend supports CORS configuration in `config/config.yaml`:

```yaml
api:
  cors_enabled: true  # Enable for development
  # cors_enabled: false  # Disable for production
```

### Authentication
Consider implementing authentication for production:
- JWT tokens
- API keys
- Session-based auth

### Rate Limiting
Implement rate limiting on the frontend to avoid overwhelming the API.

## 🧪 Testing Frontend Integration

### Mock API Server
For frontend development without the full backend:

```javascript
// Mock API responses for development
const mockAPI = {
  '/api/status': {
    running: true,
    packets_processed: 1500,
    alerts_generated: 5
  },
  '/api/alerts': {
    alerts: [
      {
        id: 'mock-1',
        severity: 'medium',
        description: 'Mock alert for testing'
      }
    ]
  }
};
```

### Integration Tests
```javascript
// Test API connectivity
async function testAPIConnection() {
  try {
    const response = await fetch('/api/health');
    const health = await response.json();
    console.log('API Health:', health);
    return health.status === 'healthy';
  } catch (error) {
    console.error('API connection failed:', error);
    return false;
  }
}
```

## 📱 Framework Examples

### React Integration
```jsx
import React, { useState, useEffect } from 'react';

function NIDSStatus() {
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    const fetchStatus = async () => {
      const response = await fetch('/api/status');
      const data = await response.json();
      setStatus(data);
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  if (!status) return <div>Loading...</div>;
  
  return (
    <div className="nids-status">
      <h2>NIDS Status</h2>
      <p>Running: {status.running ? 'Yes' : 'No'}</p>
      <p>Packets Processed: {status.packets_processed}</p>
      <p>Alerts: {status.alerts_generated}</p>
    </div>
  );
}
```

### Vue.js Integration
```vue
<template>
  <div class="nids-dashboard">
    <h1>NIDS Dashboard</h1>
    <div v-if="status">
      <p>Status: {{ status.running ? 'Running' : 'Stopped' }}</p>
      <p>Packets: {{ status.packets_processed }}</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      status: null
    };
  },
  async mounted() {
    await this.fetchStatus();
    setInterval(this.fetchStatus, 5000);
  },
  methods: {
    async fetchStatus() {
      const response = await fetch('/api/status');
      this.status = await response.json();
    }
  }
};
</script>
```

## 🚀 Deployment

### Development
```bash
# Start backend API
cd backend
python main.py --api --port 8000

# Start frontend dev server (example)
cd frontend
npm run dev
```

### Production
```bash
# Backend with production config
python main.py --api --config config/production.yaml

# Frontend build
npm run build
```

This integration guide provides everything needed to build a comprehensive frontend for the NIDS Backend!