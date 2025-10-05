"""
Alerts Widget - Real-time alerts display and management
Shows recent security alerts with filtering and details
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QPushButton, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QColor
from loguru import logger


class AlertsTable(QTableWidget):
    """Table widget for displaying alerts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()
        self._apply_styling()
    
    def _setup_table(self):
        """Setup table structure"""
        # Define columns
        self.columns = [
            "Time", "Severity", "Type", "Source", "Target", 
            "Confidence", "Interface", "Description"
        ]
        
        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels(self.columns)
        
        # Configure table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setSortingEnabled(True)
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Severity
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Source
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Target
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Confidence
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Interface
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # Description
    
    def _apply_styling(self):
        """Apply table styling"""
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                alternate-background-color: #2c3e50;
                color: #ffffff;
                gridline-color: #3498db;
                border: 1px solid #3498db;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
            
            QTableWidget::item {
                padding: 5px;
                border: none;
            }
            
            QTableWidget::item:selected {
                background-color: #e94560;
                color: #ffffff;
            }
            
            QHeaderView::section {
                background-color: #34495e;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #3498db;
                font-weight: bold;
            }
            
            QScrollBar:vertical {
                background-color: #2c3e50;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #3498db;
                border-radius: 6px;
                min-height: 20px;
            }
        """)
    
    def add_alert(self, alert_data: Dict[str, Any]):
        """Add alert to table"""
        try:
            row = self.rowCount()
            self.insertRow(row)
            
            # Format timestamp
            timestamp = alert_data.get('timestamp', time.time())
            if isinstance(timestamp, (int, float)):
                time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            else:
                time_str = str(timestamp)[:8]  # Truncate if string
            
            # Create items
            items = [
                time_str,
                alert_data.get('severity', 'unknown').upper(),
                alert_data.get('attack_type', 'Unknown'),
                alert_data.get('source_ip', 'N/A'),
                f"{alert_data.get('destination_ip', 'N/A')}:{alert_data.get('destination_port', 'N/A')}",
                f"{alert_data.get('confidence', 0):.2f}",
                alert_data.get('extra', {}).get('iface', 'N/A'),  # Interface from extra field
                alert_data.get('description', 'No description')
            ]
            
            # Add items to table
            for col, item_text in enumerate(items):
                item = QTableWidgetItem(str(item_text))
                
                # Color code by severity
                severity = alert_data.get('severity', 'unknown').lower()
                if severity == 'critical':
                    item.setBackground(QColor(231, 76, 60, 50))  # Red
                elif severity == 'high':
                    item.setBackground(QColor(241, 196, 15, 50))  # Yellow
                elif severity == 'medium':
                    item.setBackground(QColor(52, 152, 219, 50))  # Blue
                else:
                    item.setBackground(QColor(149, 165, 166, 30))  # Gray
                
                self.setItem(row, col, item)
            
            # Auto-scroll to latest
            self.scrollToBottom()
            
            # Limit table size (keep last 1000 alerts)
            if self.rowCount() > 1000:
                self.removeRow(0)
            
        except Exception as e:
            logger.error(f"Failed to add alert to table: {e}")
    
    def clear_alerts(self):
        """Clear all alerts from table"""
        self.setRowCount(0)
    
    def get_selected_alert(self) -> Optional[Dict[str, str]]:
        """Get currently selected alert data"""
        current_row = self.currentRow()
        if current_row < 0:
            return None
        
        alert_data = {}
        for col, column_name in enumerate(self.columns):
            item = self.item(current_row, col)
            alert_data[column_name.lower()] = item.text() if item else ""
        
        return alert_data


class AlertsWidget(QWidget):
    """
    Alerts display widget with real-time updates
    """
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.log_file_path = None
        self.last_file_size = 0
        
        self._setup_ui()
        self._apply_styling()
        self._setup_timers()
    
    def _setup_ui(self):
        """Setup alerts UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🚨 SECURITY ALERTS")
        title_label.setObjectName("section_title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_alerts)
        header_layout.addWidget(self.clear_button)
        
        layout.addLayout(header_layout)
        
        # Splitter for table and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Alerts table
        self.alerts_table = AlertsTable()
        self.alerts_table.itemSelectionChanged.connect(self._on_alert_selected)
        splitter.addWidget(self.alerts_table)
        
        # Alert details
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(100)
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select an alert to view details...")
        splitter.addWidget(self.details_text)
        
        # Set splitter proportions
        splitter.setSizes([400, 100])
        
        layout.addWidget(splitter)
    
    def _apply_styling(self):
        """Apply widget styling"""
        self.setStyleSheet("""
            AlertsWidget {
                background-color: #1a1a2e;
                border-radius: 10px;
                padding: 5px;
            }
            
            QLabel#section_title {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
                padding: 5px;
                background-color: rgba(233, 69, 96, 0.2);
                border-radius: 5px;
            }
            
            QPushButton {
                background-color: #e94560;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                max-width: 60px;
            }
            
            QPushButton:hover {
                background-color: #c73650;
            }
            
            QTextEdit {
                background-color: #2c3e50;
                color: #ffffff;
                border: 1px solid #3498db;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                padding: 5px;
            }
        """)
    
    def _setup_timers(self):
        """Setup periodic timers"""
        # File monitoring timer
        self.file_monitor_timer = QTimer()
        self.file_monitor_timer.timeout.connect(self._check_log_file)
        self.file_monitor_timer.start(1000)  # Check every second
        
        # API alerts refresh timer
        self.api_refresh_timer = QTimer()
        self.api_refresh_timer.timeout.connect(self._refresh_api_alerts)
        self.api_refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def _check_log_file(self):
        """Check for new alerts in log file"""
        try:
            if not self.log_file_path:
                return
            
            log_path = Path(self.log_file_path)
            if not log_path.exists():
                return
            
            current_size = log_path.stat().st_size
            if current_size > self.last_file_size:
                # File has grown, read new content
                self._read_new_alerts(log_path)
                self.last_file_size = current_size
            
        except Exception as e:
            logger.error(f"Failed to check log file: {e}")
    
    def _read_new_alerts(self, log_path: Path):
        """Read new alerts from log file"""
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_file_size)
                new_lines = f.readlines()
            
            for line in new_lines:
                line = line.strip()
                if line:
                    try:
                        alert_data = json.loads(line)
                        self.alerts_table.add_alert(alert_data)
                    except json.JSONDecodeError:
                        continue
            
        except Exception as e:
            logger.error(f"Failed to read new alerts: {e}")
    
    def _refresh_api_alerts(self):
        """Refresh alerts from API"""
        try:
            alerts = self.api_client.get_recent_alerts(50)  # Get last 50 alerts
            if alerts:
                # Clear table and reload (simple approach)
                # In production, you'd want to merge intelligently
                pass  # File monitoring handles this better
                
        except Exception as e:
            logger.debug(f"API alerts refresh failed: {e}")
    
    def _clear_alerts(self):
        """Clear all alerts from display"""
        self.alerts_table.clear_alerts()
        self.details_text.clear()
        logger.info("Alerts display cleared")
    
    def _on_alert_selected(self):
        """Handle alert selection"""
        selected_alert = self.alerts_table.get_selected_alert()
        if selected_alert:
            # Format details
            details = []
            for key, value in selected_alert.items():
                details.append(f"{key.title()}: {value}")
            
            self.details_text.setPlainText("\\n".join(details))
    
    def refresh_alerts(self):
        """Refresh alerts display"""
        # Update log file path from stats
        try:
            stats = self.api_client.get_stats()
            if stats:
                self.log_file_path = stats.get('logfile_path')
                if self.log_file_path and Path(self.log_file_path).exists():
                    self.last_file_size = Path(self.log_file_path).stat().st_size
        except Exception as e:
            logger.debug(f"Failed to refresh log file path: {e}")
    
    def set_log_file_path(self, path: str):
        """Set alerts log file path"""
        self.log_file_path = path
        self.last_file_size = 0
        if Path(path).exists():
            self.last_file_size = Path(path).stat().st_size
        logger.info(f"Alerts log file set to: {path}")