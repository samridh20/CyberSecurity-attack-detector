"""
Stats Widget - Real-time statistics display
Shows packets per second, alerts, and system metrics
"""

from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from loguru import logger


class StatCard(QFrame):
    """Individual statistic card"""
    
    def __init__(self, title: str, value: str = "0", unit: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setObjectName("stat_title")
        layout.addWidget(self.title_label)
        
        # Value and unit
        value_layout = QHBoxLayout()
        self.value_label = QLabel(value)
        self.value_label.setObjectName("stat_value")
        value_layout.addWidget(self.value_label)
        
        if unit:
            self.unit_label = QLabel(unit)
            self.unit_label.setObjectName("stat_unit")
            value_layout.addWidget(self.unit_label)
        
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        self._apply_styling()
    
    def _apply_styling(self):
        """Apply card styling"""
        self.setStyleSheet("""
            StatCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
                border: 2px solid #3498db;
                border-radius: 8px;
                margin: 2px;
            }
            
            QLabel#stat_title {
                color: #bdc3c7;
                font-size: 11px;
                font-weight: bold;
            }
            
            QLabel#stat_value {
                color: #00ff88;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            }
            
            QLabel#stat_unit {
                color: #95a5a6;
                font-size: 12px;
                margin-left: 5px;
            }
        """)
    
    def update_value(self, value: str):
        """Update the displayed value"""
        self.value_label.setText(value)


class StatsWidget(QWidget):
    """
    Statistics display widget showing real-time metrics
    """
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup stats UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("📊 SYSTEM STATISTICS")
        title_label.setObjectName("section_title")
        layout.addWidget(title_label)
        
        # Stats grid
        stats_layout = QGridLayout()
        
        # Create stat cards
        self.pps_card = StatCard("Packets/Sec", "0", "pps")
        self.alerts_card = StatCard("Alerts/Sec", "0.00", "aps")
        self.total_packets_card = StatCard("Total Packets", "0")
        self.total_alerts_card = StatCard("Total Alerts", "0")
        self.flows_card = StatCard("Active Flows", "0")
        self.uptime_card = StatCard("Uptime", "0", "sec")
        
        # Add to grid
        stats_layout.addWidget(self.pps_card, 0, 0)
        stats_layout.addWidget(self.alerts_card, 0, 1)
        stats_layout.addWidget(self.total_packets_card, 1, 0)
        stats_layout.addWidget(self.total_alerts_card, 1, 1)
        stats_layout.addWidget(self.flows_card, 2, 0)
        stats_layout.addWidget(self.uptime_card, 2, 1)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
    
    def _apply_styling(self):
        """Apply widget styling"""
        self.setStyleSheet("""
            StatsWidget {
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
        """)
    
    def update_stats(self, stats_data: Dict[str, Any]):
        """Update statistics display"""
        try:
            # Update individual cards
            pps = stats_data.get('pps', 0)
            self.pps_card.update_value(f"{pps:.1f}")
            
            alerts_per_sec = stats_data.get('alerts_per_sec', 0)
            self.alerts_card.update_value(f"{alerts_per_sec:.3f}")
            
            total_packets = stats_data.get('packets_processed', 0)
            self.total_packets_card.update_value(f"{total_packets:,}")
            
            total_alerts = stats_data.get('alerts_generated', 0)
            self.total_alerts_card.update_value(f"{total_alerts:,}")
            
            active_flows = stats_data.get('active_flows', 0)
            self.flows_card.update_value(f"{active_flows}")
            
            uptime = stats_data.get('uptime_seconds', 0)
            self.uptime_card.update_value(f"{int(uptime)}")
            
            logger.debug(f"Stats updated: {pps:.1f} pps, {total_alerts} alerts")
            
        except Exception as e:
            logger.error(f"Failed to update stats: {e}")
    
    def get_current_stats(self) -> Dict[str, str]:
        """Get current displayed statistics"""
        return {
            "pps": self.pps_card.value_label.text(),
            "alerts_per_sec": self.alerts_card.value_label.text(),
            "total_packets": self.total_packets_card.value_label.text(),
            "total_alerts": self.total_alerts_card.value_label.text(),
            "active_flows": self.flows_card.value_label.text(),
            "uptime": self.uptime_card.value_label.text()
        }