# NIDS PyQt6 Frontend

Spider-Verse themed desktop monitor for the Network Intrusion Detection System.

## Features

- **Real-time monitoring**: Live display of network traffic and security alerts
- **Interface hot-swapping**: Change network capture interface without restart
- **Spider-Verse theme**: Dark theme with neon accents and glitch effects
- **Real-time charts**: Traffic visualization using pyqtgraph
- **Alert management**: Live alert display with severity color coding
- **Configuration sync**: Read-only config display with interface editing
- **Windows notifications**: Toast notifications for alerts and status changes

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the backend is running with API server:
```bash
cd ../backend
python -m api.server --port 8000
```

## Usage

### Starting the UI

```bash
python main.py
```

### Changing Network Interface

1. Go to the **Settings** tab
2. Select a new interface from the dropdown
3. Click **Apply**
4. The backend will reload with the new interface
5. Status updates will show in the header

### Error Handling

- **Connection errors**: Red status chip, error banner in header
- **Interface change failures**: Config rollback, error notification
- **API timeouts**: Automatic retry with backoff (250ms, 500ms, 1s)

## Architecture

### Components

- **HeaderWidget**: Status display with connection indicator
- **StatsWidget**: Real-time system statistics
- **AlertsWidget**: Live alert display with file monitoring
- **ChartsWidget**: Traffic and alert visualization
- **SettingsWidget**: Interface selection and config display

### Data Flow

1. **API Client** polls backend every second for stats
2. **Config Manager** handles YAML file editing with ruamel.yaml
3. **Alert Widget** monitors `alerts.jsonl` for new entries
4. **Interface changes** update config → call API → update UI

### Error Recovery

- **API failures**: 3 retries with exponential backoff
- **Interface failures**: Automatic rollback to previous interface
- **Config errors**: Preserve original file, show error notifications

## Configuration

The UI reads configuration from `../backend/config.yaml`:

```yaml
capture:
  interface: "Ethernet"  # Only this field is editable from UI
  filter: "tcp or udp"
  # ... other fields are read-only
```

## File Monitoring

The UI monitors rotating log files:
- `alerts.jsonl`
- `alerts.jsonl.1` 
- `alerts.jsonl.2`
- etc.

New alerts appear in real-time without polling the API.

## Theming

Spider-Verse theme features:
- Dark backgrounds (#1a1a2e, #16213e, #0f3460)
- Neon accents (#e94560, #3498db, #00ff88)
- Glitch effects on title every 5 seconds
- Monospace fonts for technical data

## Development

### Adding New Widgets

1. Create widget in `ui/widgets/`
2. Add to main window layout
3. Connect API client signals
4. Apply Spider theme styling

### Extending API Integration

1. Add methods to `NIDSAPIClient`
2. Define request/response models
3. Handle errors with retry logic
4. Emit Qt signals for UI updates

## Troubleshooting

### Backend Connection Issues

- Check if backend API is running on port 8000
- Verify firewall settings
- Check backend logs for errors

### Interface Change Failures

- Ensure interface exists and is accessible
- Check backend permissions for interface access
- Verify config file is writable

### Missing Alerts

- Check `alerts.jsonl` file exists and is readable
- Verify log file path in backend config
- Check file permissions

## Dependencies

- **PyQt6**: GUI framework
- **pyqtgraph**: Real-time plotting
- **requests**: HTTP client for API calls
- **ruamel.yaml**: YAML editing with comment preservation
- **loguru**: Structured logging
- **winrt** (Windows): Native toast notifications