"""
API Client for NIDS Backend
Handles all communication with the FastAPI backend
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from loguru import logger


class NIDSAPIClient(QObject):
    """
    API client for NIDS backend with retry logic and error handling
    """
    
    # Signals for UI updates
    health_updated = pyqtSignal(dict)
    stats_updated = pyqtSignal(dict)
    interfaces_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str, str)  # error_type, message
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.25,  # 250ms, 500ms, 1s
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set timeout
        self.timeout = 1.5
        
        # Status tracking
        self.last_health_check = 0
        self.is_backend_available = False
        
        # Setup periodic health checks
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.check_health)
        self.health_timer.start(5000)  # Check every 5 seconds
        
        # Setup stats updates
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.get_stats)
        self.stats_timer.start(1000)  # Update every second
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        Make HTTP request with error handling and retries
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data or None if failed
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            
            # Mark backend as available
            if not self.is_backend_available:
                self.is_backend_available = True
                logger.info("Backend connection restored")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout to {endpoint}"
            logger.warning(error_msg)
            self._handle_error("timeout", error_msg)
            return None
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection error to {endpoint}"
            if self.is_backend_available:
                logger.error(error_msg)
                self.is_backend_available = False
            self._handle_error("connection", error_msg)
            return None
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code} for {endpoint}: {e.response.text}"
            logger.error(error_msg)
            self._handle_error("http", error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error for {endpoint}: {str(e)}"
            logger.error(error_msg)
            self._handle_error("unknown", error_msg)
            return None
    
    def _handle_error(self, error_type: str, message: str):
        """Handle API errors and emit signals"""
        self.error_occurred.emit(error_type, message)
    
    def check_health(self) -> Optional[Dict]:
        """Check backend health status"""
        health_data = self._make_request("GET", "/health")
        if health_data:
            self.health_updated.emit(health_data)
            self.last_health_check = time.time()
        return health_data
    
    def get_interfaces(self) -> Optional[List[str]]:
        """Get available network interfaces"""
        interfaces = self._make_request("GET", "/capture/interfaces")
        if interfaces:
            self.interfaces_updated.emit(interfaces)
        return interfaces
    
    def reload_interface(self, interface: str) -> Optional[Dict]:
        """
        Reload capture with new interface
        
        Args:
            interface: Network interface name
            
        Returns:
            Response data or None if failed
        """
        data = {"iface": interface}
        response = self._make_request("POST", "/capture/reload", json=data)
        
        if response:
            logger.info(f"Interface reloaded to: {interface}")
        
        return response
    
    def get_stats(self) -> Optional[Dict]:
        """Get system statistics"""
        stats = self._make_request("GET", "/stats")
        if stats:
            self.stats_updated.emit(stats)
        return stats
    
    def get_recent_alerts(self, limit: int = 100) -> Optional[List[Dict]]:
        """Get recent alerts"""
        return self._make_request("GET", f"/alerts/recent?limit={limit}")
    
    def get_config(self) -> Optional[Dict]:
        """Get current configuration"""
        return self._make_request("GET", "/config")
    
    def is_connected(self) -> bool:
        """Check if backend is connected"""
        return self.is_backend_available and (time.time() - self.last_health_check) < 10
    
    def get_connection_status(self) -> str:
        """Get connection status string"""
        if not self.is_backend_available:
            return "disconnected"
        elif (time.time() - self.last_health_check) > 10:
            return "stale"
        else:
            return "connected"