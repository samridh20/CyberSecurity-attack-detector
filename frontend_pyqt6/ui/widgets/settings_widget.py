"""
Settings Widget - Configuration and interface management
Handles network interface selection and config display
"""

from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QTextEdit, QFrame,
    QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont
from loguru import logger


class InterfaceSelector(QFrame):
    """Network interface selection widget"""
    
    interface_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_interface = "auto"
        self.available_interfaces = []
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup interface selector UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel("🌐 Network Interface")
        title_label.setObjectName("selector_title")
        layout.addWidget(title_label)
        
        # Interface selection
        selection_layout = QHBoxLayout()
        
        self.interface_combo = QComboBox()
        self.interface_combo.setMinimumWidth(200)
        self.interface_combo.currentTextChanged.connect(self._on_interface_changed)
        selection_layout.addWidget(self.interface_combo)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self._apply_interface_change)
        selection_layout.addWidget(self.apply_button)
        
        layout.addLayout(selection_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)
    
    def _apply_styling(self):
        """Apply styling to interface selector"""
        self.setStyleSheet("""
            InterfaceSelector {
                background-color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin: 5px;
            }
            
            QLabel#selector_title {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            QComboBox {
                background-color: #34495e;
                color: #ffffff;
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Courier New', monospace;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #3498db;
            }
            
            QPushButton {
                background-color: #e94560;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #c73650;
            }
            
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
            
            QLabel#status {
                color: #95a5a6;
                font-size: 10px;
                margin-top: 5px;
            }
        """)
    
    def update_interfaces(self, interfaces: List[str]):
        """Update available interfaces"""
        self.available_interfaces = interfaces
        
        # Clear and repopulate combo box
        self.interface_combo.clear()
        self.interface_combo.addItems(interfaces)
        
        # Set current interface if available
        if self.current_interface in interfaces:
            self.interface_combo.setCurrentText(self.current_interface)
        
        logger.info(f"Updated interfaces: {interfaces}")
    
    def set_current_interface(self, interface: str):
        """Set current active interface"""
        self.current_interface = interface
        if interface in self.available_interfaces:
            self.interface_combo.setCurrentText(interface)
        self.apply_button.setEnabled(False)
        self.status_label.setText(f"Active: {interface}")
    
    def _on_interface_changed(self, interface: str):
        """Handle interface selection change"""
        if interface != self.current_interface:
            self.apply_button.setEnabled(True)
            self.status_label.setText(f"Ready to change to: {interface}")
        else:
            self.apply_button.setEnabled(False)
            self.status_label.setText(f"Active: {interface}")
    
    def _apply_interface_change(self):
        """Apply interface change"""
        selected_interface = self.interface_combo.currentText()
        if selected_interface and selected_interface != self.current_interface:
            self.apply_button.setEnabled(False)
            self.status_label.setText("Applying change...")
            self.interface_selected.emit(selected_interface)
    
    def show_error(self, message: str):
        """Show error status"""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: #e74c3c;")
        self.apply_button.setEnabled(True)
        
        # Clear error after 5 seconds
        QTimer.singleShot(5000, self._clear_error)
    
    def show_success(self, interface: str):
        """Show success status"""
        self.current_interface = interface
        self.status_label.setText(f"Successfully changed to: {interface}")
        self.status_label.setStyleSheet("color: #00ff88;")
        self.apply_button.setEnabled(False)
        
        # Clear success message after 3 seconds
        QTimer.singleShot(3000, self._clear_status)
    
    def _clear_error(self):
        """Clear error styling"""
        self.status_label.setStyleSheet("color: #95a5a6;")
        self.status_label.setText(f"Active: {self.current_interface}")
    
    def _clear_status(self):
        """Clear status styling"""
        self.status_label.setStyleSheet("color: #95a5a6;")
        self.status_label.setText(f"Active: {self.current_interface}")


class ConfigDisplay(QFrame):
    """Configuration display widget (read-only)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup config display UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel("⚙️ Configuration (Read-Only)")
        title_label.setObjectName("config_title")
        layout.addWidget(title_label)
        
        # Config text display
        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setMaximumHeight(300)
        layout.addWidget(self.config_text)
    
    def _apply_styling(self):
        """Apply styling to config display"""
        self.setStyleSheet("""
            ConfigDisplay {
                background-color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin: 5px;
            }
            
            QLabel#config_title {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            QTextEdit {
                background-color: #1a1a2e;
                color: #00ff88;
                border: 1px solid #3498db;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                padding: 10px;
            }
        """)
    
    def update_config(self, config_data: Dict[str, Any]):
        """Update configuration display"""
        try:
            import yaml
            config_text = yaml.dump(config_data, default_flow_style=False, indent=2)
            self.config_text.setPlainText(config_text)
        except Exception as e:
            logger.error(f"Failed to display config: {e}")
            self.config_text.setPlainText(f"Error displaying config: {e}")


class SettingsWidget(QWidget):
    """
    Settings widget for configuration and interface management
    """
    
    # Signals
    interface_change_requested = pyqtSignal(str)
    interface_changed = pyqtSignal(str)
    interface_change_failed = pyqtSignal(str)
    
    def __init__(self, config_manager, api_client, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.api_client = api_client
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styling()
        
        # Load initial data
        self._load_initial_data()
    
    def _setup_ui(self):
        """Setup settings UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Interface selector
        self.interface_selector = InterfaceSelector()
        scroll_layout.addWidget(self.interface_selector)
        
        # Configuration display
        self.config_display = ConfigDisplay()
        scroll_layout.addWidget(self.config_display)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.interface_selector.interface_selected.connect(self.interface_change_requested.emit)
        self.api_client.interfaces_updated.connect(self.interface_selector.update_interfaces)
    
    def _apply_styling(self):
        """Apply widget styling"""
        self.setStyleSheet("""
            SettingsWidget {
                background-color: #1a1a2e;
                border-radius: 10px;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
    
    def _load_initial_data(self):
        """Load initial settings data"""
        # Get current interface from config
        current_interface = self.config_manager.get_capture_interface() or "auto"
        self.interface_selector.set_current_interface(current_interface)
        
        # Get available interfaces
        self.api_client.get_interfaces()
        
        # Display current config
        config_data = self.config_manager.get_config()
        self.config_display.update_config(config_data)
    
    @pyqtSlot(str)
    def on_interface_changed(self, interface: str):
        """Handle successful interface change"""
        self.interface_selector.show_success(interface)
        self.interface_changed.emit(interface)
    
    @pyqtSlot(str)
    def on_interface_change_failed(self, error_message: str):
        """Handle failed interface change"""
        self.interface_selector.show_error(error_message)
        self.interface_change_failed.emit(error_message)
    
    def update_config_display(self, config_data: Dict[str, Any]):
        """Update configuration display"""
        self.config_display.update_config(config_data)
        
        # Update current interface
        capture_config = config_data.get('capture', {})
        current_interface = capture_config.get('interface', 'auto')
        self.interface_selector.set_current_interface(current_interface)