"""
Main Window for NIDS PyQt6 Frontend
Spider-Verse themed desktop monitor with real-time data
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor
from loguru import logger

from .widgets.header_widget import HeaderWidget
from .widgets.alerts_widget import AlertsWidget
from .widgets.stats_widget import StatsWidget
from .widgets.settings_widget import SettingsWidget
from .widgets.charts_widget import ChartsWidget
from .style.spider_theme import SpiderTheme
from .utils.notifications import NotificationManager
from core.config_manager import ConfigManager
from core.api_client import NIDSAPIClient


class NIDSMainWindow(QMainWindow):
    """
    Main window for NIDS monitoring application
    Spider-Verse themed with real-time data integration
    """
    
    def __init__(self, config_manager: ConfigManager, api_client: NIDSAPIClient):
        super().__init__()
        self.config_manager = config_manager
        self.api_client = api_client
        self.notification_manager = NotificationManager()
        
        # Window properties
        self.setWindowTitle("NIDS Monitor - Spider-Verse Edition")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Apply Spider-Verse theme
        self.theme = SpiderTheme()
        self.setStyleSheet(self.theme.get_main_stylesheet())
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        self._setup_timers()
        
        # Initial data load
        self._load_initial_data()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header
        self.header_widget = HeaderWidget(self.api_client)
        main_layout.addWidget(self.header_widget)
        
        # Content splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # Left panel - Alerts and Stats
        left_panel = self._create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Right panel - Charts and Settings
        right_panel = self._create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        content_splitter.setSizes([600, 800])
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with alerts and stats"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Stats widget
        self.stats_widget = StatsWidget(self.api_client)
        layout.addWidget(self.stats_widget)
        
        # Alerts widget
        self.alerts_widget = AlertsWidget(self.api_client)
        layout.addWidget(self.alerts_widget)
        
        # Set proportions
        layout.setStretch(0, 1)  # Stats
        layout.setStretch(1, 2)  # Alerts (larger)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with charts and settings"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Tab widget for charts and settings
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(self.theme.get_tab_stylesheet())
        
        # Charts tab
        self.charts_widget = ChartsWidget(self.api_client)
        tab_widget.addTab(self.charts_widget, "📊 Charts")
        
        # Settings tab
        self.settings_widget = SettingsWidget(self.config_manager, self.api_client)
        tab_widget.addTab(self.settings_widget, "⚙️ Settings")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def _connect_signals(self):
        """Connect signals between components"""
        # API client signals
        self.api_client.health_updated.connect(self._on_health_updated)
        self.api_client.stats_updated.connect(self._on_stats_updated)
        self.api_client.error_occurred.connect(self._on_api_error)
        
        # Config manager signals
        self.config_manager.config_changed.connect(self._on_config_changed)
        self.config_manager.config_error.connect(self._on_config_error)
        
        # Settings widget signals
        self.settings_widget.interface_change_requested.connect(self._on_interface_change_requested)
        self.settings_widget.interface_changed.connect(self._on_interface_changed)
        self.settings_widget.interface_change_failed.connect(self._on_interface_change_failed)
    
    def _setup_timers(self):
        """Setup periodic update timers"""
        # Glitch effect timer
        self.glitch_timer = QTimer()
        self.glitch_timer.timeout.connect(self._apply_glitch_effect)
        self.glitch_timer.start(5000)  # Every 5 seconds
        
        # Data refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_data)
        self.refresh_timer.start(1000)  # Every second
    
    def _load_initial_data(self):
        """Load initial data from API"""
        # Check health
        self.api_client.check_health()
        
        # Get interfaces
        self.api_client.get_interfaces()
        
        # Get initial stats
        self.api_client.get_stats()
    
    @pyqtSlot(dict)
    def _on_health_updated(self, health_data: Dict[str, Any]):
        """Handle health status updates"""
        self.header_widget.update_health_status(health_data)
        logger.debug(f"Health updated: {health_data.get('status', 'unknown')}")
    
    @pyqtSlot(dict)
    def _on_stats_updated(self, stats_data: Dict[str, Any]):
        """Handle stats updates"""
        self.stats_widget.update_stats(stats_data)
        self.charts_widget.update_charts(stats_data)
        logger.debug(f"Stats updated: {stats_data.get('pps', 0)} pps")
    
    @pyqtSlot(str, str)
    def _on_api_error(self, error_type: str, message: str):
        """Handle API errors"""
        self.header_widget.show_error(error_type, message)
        
        # Show notification for critical errors
        if error_type in ['connection', 'timeout']:
            self.notification_manager.show_error(
                "Backend Connection Error",
                "Lost connection to NIDS backend"
            )
    
    @pyqtSlot(dict)
    def _on_config_changed(self, config_data: Dict[str, Any]):
        """Handle configuration changes"""
        logger.info("Configuration updated")
        self.settings_widget.update_config_display(config_data)
    
    @pyqtSlot(str)
    def _on_config_error(self, error_message: str):
        """Handle configuration errors"""
        logger.error(f"Configuration error: {error_message}")
        self.notification_manager.show_error("Configuration Error", error_message)
    
    @pyqtSlot(str)
    def _on_interface_change_requested(self, interface: str):
        """Handle interface change request"""
        logger.info(f"Interface change requested: {interface}")
        
        # Update config file first
        if self.config_manager.set_capture_interface(interface):
            if self.config_manager.save_config():
                # Call API to reload
                response = self.api_client.reload_interface(interface)
                if response and response.get('ok'):
                    self.settings_widget.interface_changed.emit(interface)
                    self.notification_manager.show_success(
                        "Interface Changed",
                        f"Successfully changed to {interface}"
                    )
                else:
                    # Rollback on API failure
                    self._rollback_interface_change(interface)
            else:
                self.settings_widget.interface_change_failed.emit("Failed to save configuration")
        else:
            self.settings_widget.interface_change_failed.emit("Failed to update configuration")
    
    @pyqtSlot(str)
    def _on_interface_changed(self, interface: str):
        """Handle successful interface change"""
        logger.info(f"Interface successfully changed to: {interface}")
        self.header_widget.update_active_interface(interface)
    
    @pyqtSlot(str)
    def _on_interface_change_failed(self, error_message: str):
        """Handle failed interface change"""
        logger.error(f"Interface change failed: {error_message}")
        self.notification_manager.show_error("Interface Change Failed", error_message)
    
    def _rollback_interface_change(self, failed_interface: str):
        """Rollback interface change on failure"""
        # Get current active interface from health check
        health_data = self.api_client.check_health()
        if health_data:
            active_interface = health_data.get('active_iface', 'auto')
            self.config_manager.rollback_interface(active_interface)
            self.config_manager.save_config()
            
            self.settings_widget.interface_change_failed.emit(
                f"Failed to change to {failed_interface}, rolled back to {active_interface}"
            )
    
    def _apply_glitch_effect(self):
        """Apply Spider-Verse glitch effect"""
        # This could animate some UI elements with glitch effects
        # For now, just update the theme colors slightly
        self.theme.apply_glitch_effect()
        
        # Update specific widgets with glitch
        self.header_widget.apply_glitch_effect()
    
    def _refresh_data(self):
        """Refresh data from backend"""
        # This is handled by the API client timers
        # Just ensure alerts are updated
        self.alerts_widget.refresh_alerts()
    
    def closeEvent(self, event):
        """Handle window close event"""
        logger.info("Shutting down NIDS UI")
        
        # Stop timers
        self.glitch_timer.stop()
        self.refresh_timer.stop()
        
        # Save any pending configuration
        if self.config_manager.is_valid():
            self.config_manager.save_config()
        
        event.accept()