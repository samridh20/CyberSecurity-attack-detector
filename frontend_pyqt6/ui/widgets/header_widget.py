"""
Header Widget - Status display and branding
Spider-Verse themed header with status indicators
"""

import time
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QFrame, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor
from loguru import logger


class StatusChip(QWidget):
    """Status indicator chip with color coding"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 30)
        self.status = "unknown"
        self.active_interface = "auto"
        
    def set_status(self, status: str, interface: str = "auto"):
        """Update status and interface"""
        self.status = status
        self.active_interface = interface
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for status chip"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Determine colors based on status
        if self.status == "healthy":
            bg_color = QColor(46, 204, 113)  # Green
            text_color = QColor(255, 255, 255)
        elif self.status == "degraded":
            bg_color = QColor(241, 196, 15)  # Amber
            text_color = QColor(0, 0, 0)
        else:
            bg_color = QColor(231, 76, 60)  # Red
            text_color = QColor(255, 255, 255)
        
        # Draw background
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        
        # Draw text
        painter.setPen(text_color)
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        status_text = self.status.upper()
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, status_text)


class HeaderWidget(QWidget):
    """
    Header widget with branding, status, and connection info
    """
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.error_message = ""
        self.error_timer = QTimer()
        self.error_timer.timeout.connect(self._clear_error)
        
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup header UI layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Left side - Branding
        left_layout = QVBoxLayout()
        
        # Title with Spider-Verse styling
        self.title_label = QLabel("NIDS MONITOR")
        self.title_label.setObjectName("title")
        left_layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel("Network Intrusion Detection System")
        self.subtitle_label.setObjectName("subtitle")
        left_layout.addWidget(self.subtitle_label)
        
        layout.addLayout(left_layout)
        
        # Spacer
        layout.addStretch()
        
        # Center - Status info
        center_layout = QVBoxLayout()
        
        # Active interface
        self.interface_label = QLabel("Interface: auto")
        self.interface_label.setObjectName("interface")
        center_layout.addWidget(self.interface_label)
        
        # Connection status
        self.connection_label = QLabel("Connecting...")
        self.connection_label.setObjectName("connection")
        center_layout.addWidget(self.connection_label)
        
        layout.addLayout(center_layout)
        
        # Right side - Status chip and error display
        right_layout = QVBoxLayout()
        
        # Status chip
        self.status_chip = StatusChip()
        right_layout.addWidget(self.status_chip, alignment=Qt.AlignmentFlag.AlignRight)
        
        # Error message (initially hidden)
        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)
        self.error_label.setMaximumWidth(300)
        right_layout.addWidget(self.error_label)
        
        layout.addLayout(right_layout)
    
    def _apply_styling(self):
        """Apply Spider-Verse themed styling"""
        self.setStyleSheet("""
            HeaderWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border-bottom: 3px solid #e94560;
                border-radius: 10px;
                margin-bottom: 5px;
            }
            
            QLabel#title {
                font-family: 'Arial Black', Arial, sans-serif;
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                text-shadow: 2px 2px 4px rgba(233, 69, 96, 0.5);
            }
            
            QLabel#subtitle {
                font-family: Arial, sans-serif;
                font-size: 12px;
                color: #b0b0b0;
                margin-top: -5px;
            }
            
            QLabel#interface {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                color: #00ff88;
                font-weight: bold;
            }
            
            QLabel#connection {
                font-family: Arial, sans-serif;
                font-size: 10px;
                color: #888888;
            }
            
            QLabel#error {
                background-color: rgba(231, 76, 60, 0.2);
                border: 1px solid #e74c3c;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
                font-size: 10px;
            }
        """)
    
    def update_health_status(self, health_data: Dict[str, Any]):
        """Update health status display"""
        status = health_data.get('status', 'unknown')
        active_iface = health_data.get('active_iface', 'auto')
        
        # Update status chip
        self.status_chip.set_status(status, active_iface)
        
        # Update interface display
        self.interface_label.setText(f"Interface: {active_iface}")
        
        # Update connection status
        connection_status = self.api_client.get_connection_status()
        if connection_status == "connected":
            self.connection_label.setText("🟢 Connected")
            self.connection_label.setStyleSheet("color: #00ff88;")
        elif connection_status == "stale":
            self.connection_label.setText("🟡 Stale")
            self.connection_label.setStyleSheet("color: #f1c40f;")
        else:
            self.connection_label.setText("🔴 Disconnected")
            self.connection_label.setStyleSheet("color: #e74c3c;")
    
    def update_active_interface(self, interface: str):
        """Update active interface display"""
        self.interface_label.setText(f"Interface: {interface}")
        logger.info(f"Header updated with interface: {interface}")
    
    def show_error(self, error_type: str, message: str):
        """Show error message with auto-clear"""
        self.error_message = f"{error_type.upper()}: {message}"
        self.error_label.setText(self.error_message)
        self.error_label.setVisible(True)
        
        # Auto-clear after 5 seconds
        self.error_timer.start(5000)
    
    def _clear_error(self):
        """Clear error message"""
        self.error_label.setVisible(False)
        self.error_timer.stop()
    
    def apply_glitch_effect(self):
        """Apply Spider-Verse glitch effect"""
        # Simple glitch effect - briefly change title color
        original_style = self.title_label.styleSheet()
        
        # Apply glitch colors
        glitch_colors = ["#ff0080", "#00ff80", "#8000ff", "#ff8000"]
        import random
        glitch_color = random.choice(glitch_colors)
        
        glitch_style = f"""
            QLabel#title {{
                color: {glitch_color};
                text-shadow: 3px 3px 6px rgba(233, 69, 96, 0.8);
            }}
        """
        
        self.title_label.setStyleSheet(glitch_style)
        
        # Restore original style after brief delay
        QTimer.singleShot(100, lambda: self.title_label.setStyleSheet(""))
    
    def get_status_info(self) -> Dict[str, str]:
        """Get current status information"""
        return {
            "status": self.status_chip.status,
            "interface": self.status_chip.active_interface,
            "connection": self.api_client.get_connection_status(),
            "error": self.error_message
        }