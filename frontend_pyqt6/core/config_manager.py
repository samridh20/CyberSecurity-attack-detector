"""
Configuration Manager for NIDS Frontend
Handles YAML configuration with in-place editing using ruamel.yaml
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ruamel.yaml import YAML
from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger


class ConfigManager(QObject):
    """
    Configuration manager with in-place YAML editing
    Preserves comments and formatting when updating config files
    """
    
    # Signals
    config_changed = pyqtSignal(dict)
    config_error = pyqtSignal(str)
    
    def __init__(self, config_path: str = "../backend/config.yaml", parent=None):
        super().__init__(parent)
        self.config_path = Path(config_path).resolve()
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.width = 4096  # Prevent line wrapping
        self._config_data = None
        
        # Load initial configuration
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Load configuration from YAML file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.config_path.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                self.config_error.emit(f"Configuration file not found: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = self.yaml.load(f)
            
            if self._config_data is None:
                self._config_data = {}
            
            logger.info(f"Configuration loaded from: {self.config_path}")
            self.config_changed.emit(self.get_config())
            return True
            
        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            logger.error(error_msg)
            self.config_error.emit(error_msg)
            return False
    
    def save_config(self) -> bool:
        """
        Save configuration to YAML file with preserved formatting
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(self._config_data, f)
            
            logger.info(f"Configuration saved to: {self.config_path}")
            self.config_changed.emit(self.get_config())
            return True
            
        except Exception as e:
            error_msg = f"Failed to save configuration: {e}"
            logger.error(error_msg)
            self.config_error.emit(error_msg)
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return dict(self._config_data) if self._config_data else {}
    
    def get_capture_interface(self) -> Optional[str]:
        """Get current capture interface"""
        if not self._config_data:
            return None
        
        capture_config = self._config_data.get('capture', {})
        return capture_config.get('interface')
    
    def set_capture_interface(self, interface: str) -> bool:
        """
        Set capture interface in configuration
        
        Args:
            interface: Network interface name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._config_data:
                self._config_data = {}
            
            # Ensure capture section exists
            if 'capture' not in self._config_data:
                self._config_data['capture'] = {}
            
            # Set interface
            self._config_data['capture']['interface'] = interface
            
            logger.info(f"Capture interface set to: {interface}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to set capture interface: {e}"
            logger.error(error_msg)
            self.config_error.emit(error_msg)
            return False
    
    def rollback_interface(self, interface: str) -> bool:
        """
        Rollback interface to specified value
        
        Args:
            interface: Interface to rollback to
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Rolling back interface to: {interface}")
        return self.set_capture_interface(interface)
    
    def get_alerts_config(self) -> Dict[str, Any]:
        """Get alerts configuration"""
        if not self._config_data:
            return {}
        
        return self._config_data.get('alerts', {})
    
    def get_log_file_path(self) -> str:
        """Get alerts log file path"""
        alerts_config = self.get_alerts_config()
        return alerts_config.get('log_file', 'logs/alerts.jsonl')
    
    def get_models_config(self) -> Dict[str, Any]:
        """Get models configuration"""
        if not self._config_data:
            return {}
        
        return self._config_data.get('models', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        if not self._config_data:
            return {}
        
        return self._config_data.get('performance', {})
    
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return self._config_data is not None
    
    def reload(self) -> bool:
        """Reload configuration from file"""
        return self.load_config()