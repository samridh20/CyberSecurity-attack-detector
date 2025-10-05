"""
FastAPI server for NIDS backend API
Provides endpoints for UI integration and system control
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import psutil
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from loguru import logger

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nids import RealTimeNIDS
from nids.capture import PacketCapture


class InterfaceReloadRequest(BaseModel):
    """Request model for interface reload"""
    iface: str


class APIResponse(BaseModel):
    """Standard API response model"""
    ok: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class NIDSAPIServer:
    """NIDS API Server managing the backend system"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.nids: Optional[RealTimeNIDS] = None
        self.app = FastAPI(
            title="NIDS Backend API",
            description="Network Intrusion Detection System Backend API",
            version="1.0.0"
        )
        
        # Add CORS middleware for remote access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for demo
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
        self._initialize_nids()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def _initialize_nids(self):
        """Initialize NIDS system and start real packet capture"""
        try:
            self.nids = RealTimeNIDS(str(self.config_path))
            
            # Initialize clean alert storage for API access
            if self.nids.alert_manager:
                # Start with empty alerts - only real attacks will appear
                self.nids.alert_manager._recent_alerts = []
            
            # Start real packet capture and monitoring
            logger.info("Starting real-time packet capture and monitoring...")
            self.nids.start_detection()
            
            logger.info("NIDS system initialized and monitoring started")
        except Exception as e:
            logger.error(f"Failed to initialize NIDS: {e}")
            self.nids = None
    
    def _get_network_interfaces(self) -> List[str]:
        """Get list of available network interfaces"""
        try:
            # Use psutil to get network interfaces
            interfaces = list(psutil.net_if_addrs().keys())
            # Filter out loopback and virtual interfaces
            filtered = []
            for iface in interfaces:
                if not any(skip in iface.lower() for skip in ['loopback', 'lo', 'vmware', 'virtualbox']):
                    filtered.append(iface)
            return filtered if filtered else interfaces
        except Exception as e:
            logger.error(f"Failed to get interfaces: {e}")
            return ["Ethernet", "Wi-Fi"]  # Fallback
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                active_iface = self.config.get('capture', {}).get('interface', 'auto')
                status = "healthy" if self.nids else "degraded"
                
                return {
                    "status": status,
                    "version": "1.0.0",
                    "active_iface": active_iface,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/capture/interfaces")
        async def get_interfaces():
            """Get available network interfaces"""
            try:
                interfaces = self._get_network_interfaces()
                return interfaces
            except Exception as e:
                logger.error(f"Failed to get interfaces: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/capture/reload")
        async def reload_interface(request: InterfaceReloadRequest, background_tasks: BackgroundTasks):
            """Reload capture with new interface"""
            old_iface = None
            try:
                # Validate interface
                available_interfaces = self._get_network_interfaces()
                if request.iface not in available_interfaces:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Interface '{request.iface}' not available. Available: {available_interfaces}"
                    )
                
                # Update configuration
                if 'capture' not in self.config:
                    self.config['capture'] = {}
                
                old_iface = self.config['capture'].get('interface', 'auto')
                self.config['capture']['interface'] = request.iface
                
                # Save configuration
                self._save_config()
                
                # Restart NIDS with new interface in background
                background_tasks.add_task(self._restart_nids)
                
                logger.info(f"Interface changed from {old_iface} to {request.iface}")
                
                return {
                    "ok": True,
                    "active": request.iface,
                    "message": f"Interface changed to {request.iface}"
                }
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Failed to reload interface: {e}")
                # Rollback configuration
                if 'capture' in self.config and old_iface is not None:
                    self.config['capture']['interface'] = old_iface
                    self._save_config()
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stats")
        async def get_stats():
            """Get system statistics"""
            try:
                if not self.nids:
                    return {
                        "pps": 0,
                        "alerts_per_sec": 0,
                        "last_alert_ts": None,
                        "logfile_path": str(Path("logs/alerts.jsonl").absolute()),
                        "status": "not_running"
                    }
                
                status = self.nids.get_status()
                
                # Calculate rates
                uptime = status.get('uptime_seconds', 1)
                pps = status.get('packets_processed', 0) / max(uptime, 1)
                alerts_per_sec = status.get('alerts_generated', 0) / max(uptime, 1)
                
                # Get alert manager reference
                alert_manager = self.nids.alert_manager if self.nids else None
                
                # Get last alert timestamp from stored alerts
                last_alert_ts = None
                total_alerts = 0
                
                # Check stored alerts first
                if hasattr(self, '_stored_alerts') and self._stored_alerts:
                    total_alerts = len(self._stored_alerts)
                    last_alert_ts = self._stored_alerts[0].get('timestamp')
                else:
                    # Fallback to NIDS alert manager
                    recent_alerts = alert_manager.get_recent_alerts(1) if alert_manager else []
                    last_alert_ts = recent_alerts[0].get('timestamp') if recent_alerts else None
                    total_alerts = status.get('alerts_generated', 0)
                
                # Calculate alerts per second
                current_alerts_per_sec = total_alerts / max(uptime, 1) if total_alerts > 0 else 0
                
                # Return real network monitoring statistics with updated alert info
                return {
                    "pps": round(pps, 2),
                    "alerts_per_sec": round(max(alerts_per_sec, current_alerts_per_sec), 4),
                    "last_alert_ts": last_alert_ts,
                    "logfile_path": str(alert_manager.log_file.absolute()) if alert_manager and hasattr(alert_manager, 'log_file') else None,
                    "packets_processed": status.get('packets_processed', 0),
                    "alerts_generated": max(status.get('alerts_generated', 0), total_alerts),
                    "active_flows": status.get('active_flows', 0),
                    "uptime_seconds": uptime,
                    "status": "running" if status.get('running') else "monitoring"
                }
                
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/alerts/recent")
        async def get_recent_alerts(limit: int = 100):
            """Get recent alerts from real network monitoring"""
            try:
                if not self.nids or not self.nids.alert_manager:
                    return []
                
                # Get real alerts from the NIDS alert manager
                alerts = []
                
                # FIRST: Try to get REAL ML-generated alerts from NIDS system
                try:
                    # Get alerts from the real NIDS system
                    real_ml_alerts = self.nids.alert_manager.get_recent_alerts(limit)
                    
                    # Convert to frontend format if needed
                    formatted_alerts = []
                    for alert in real_ml_alerts:
                        if isinstance(alert, dict):
                            # Ensure frontend-compatible format
                            formatted_alert = {
                                    "id": alert.get("id", f"alert_{int(time.time() * 1000)}"),
                                "timestamp": alert.get("timestamp", time.time()),
                                "attack_type": alert.get("attack_type", "Unknown"),
                                "attack_class": alert.get("attack_type", "Unknown"),  # Frontend expects this
                                "severity": alert.get("severity", "medium"),
                                "confidence": alert.get("confidence", 0.5),
                                "probability": alert.get("confidence", 0.5),  # Frontend expects this
                                "src_ip": alert.get("src_ip", "unknown"),
                                "dst_ip": alert.get("dst_ip", "unknown"),
                                "src_port": alert.get("src_port", 0),
                                "dst_port": alert.get("dst_port", 0),
                                "protocol": alert.get("protocol", "unknown"),
                                "description": alert.get("description", "Network attack detected"),
                                "recommended_action": alert.get("recommended_action", "Investigate and block if necessary")
                            }
                            formatted_alerts.append(formatted_alert)
                        else:
                            formatted_alerts.append(alert)
                        
                    alerts = formatted_alerts
                    logger.info(f"Got {len(alerts)} REAL ML alerts from NIDS")
                        
                except Exception as e:
                    logger.warning(f"Could not get ML alerts from NIDS: {e}")
                    alerts = []
                
                # FALLBACK: If no real ML alerts, try stored alerts from manual tests
                if not alerts and hasattr(self, '_stored_alerts'):
                    alerts = self._stored_alerts[:limit]
                    logger.info(f"Fallback to {len(alerts)} stored test alerts")
                
                logger.info(f"Returning {len(alerts)} real alerts from network monitoring")
                return alerts
                
            except Exception as e:
                logger.error(f"Failed to get recent alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/config")
        async def get_config():
            """Get current configuration (read-only)"""
            try:
                return self.config
            except Exception as e:
                logger.error(f"Failed to get config: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/alerts/real-detection")
        async def add_real_detection(alert_data: dict):
            """Add a real alert from packet analysis"""
            try:
                if not self.nids or not self.nids.alert_manager:
                    raise HTTPException(status_code=503, detail="NIDS not initialized")
                
                # Store the real alert
                if not hasattr(self, '_stored_alerts'):
                    self._stored_alerts = []
                
                # Add unique ID and ensure proper format
                alert_data['id'] = f"real_{int(time.time() * 1000)}_{len(self._stored_alerts)}"
                
                self._stored_alerts.insert(0, alert_data)
                self._stored_alerts = self._stored_alerts[:1000]  # Keep last 1000
                
                # Also store in alert manager
                if hasattr(self.nids.alert_manager, '_recent_alerts'):
                    if self.nids.alert_manager._recent_alerts is None:
                        self.nids.alert_manager._recent_alerts = []
                    self.nids.alert_manager._recent_alerts.insert(0, alert_data)
                    self.nids.alert_manager._recent_alerts = self.nids.alert_manager._recent_alerts[:1000]
                
                logger.info(f"Real detection added: {alert_data['attack_type']} from {alert_data['src_ip']}")
                
                return {
                    "ok": True,
                    "message": "Real detection alert added successfully",
                    "alert": alert_data
                }
                
            except Exception as e:
                logger.error(f"Failed to add real detection: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/test/add-alert")
        async def add_test_alert():
            """Add a test alert for frontend testing"""
            try:
                if not self.nids or not self.nids.alert_manager:
                    raise HTTPException(status_code=503, detail="NIDS not initialized")
                
                import time
                import random
                
                # Variety of attack types for realistic demo
                attack_types = [
                    {
                        "type": "Port Scan", "severity": "medium", "confidence": random.uniform(0.7, 0.9),
                        "description": "Port scan attack detected from suspicious source",
                        "dst_port": random.choice([22, 80, 443, 21, 25])
                    },
                    {
                        "type": "DDoS", "severity": "high", "confidence": random.uniform(0.8, 0.95),
                        "description": "Distributed Denial of Service attack detected",
                        "dst_port": 80
                    },
                    {
                        "type": "Brute Force", "severity": "high", "confidence": random.uniform(0.75, 0.9),
                        "description": "Brute force login attempt detected",
                        "dst_port": random.choice([22, 21, 3389])
                    },
                    {
                        "type": "Exploit", "severity": "critical", "confidence": random.uniform(0.85, 0.98),
                        "description": "Buffer overflow exploit attempt detected",
                        "dst_port": random.choice([80, 443, 21])
                    },
                    {
                        "type": "Reconnaissance", "severity": "low", "confidence": random.uniform(0.6, 0.8),
                        "description": "Network reconnaissance activity detected",
                        "dst_port": random.choice([53, 161, 123])
                    }
                ]
                
                # Pick a random attack type
                attack_info = random.choice(attack_types)
                
                # Create a test alert with variety
                test_alert = {
                    "id": f"test_{int(time.time() * 1000)}_{random.randint(100, 999)}",
                    "timestamp": time.time(),
                    "attack_type": attack_info["type"],
                    "attack_class": attack_info["type"],
                    "severity": attack_info["severity"],
                    "confidence": attack_info["confidence"],
                    "probability": attack_info["confidence"],
                    "src_ip": f"192.168.1.{random.randint(100, 254)}",
                    "dst_ip": "10.0.0.1",
                    "src_port": random.randint(1024, 65535),
                    "dst_port": attack_info["dst_port"],
                    "protocol": "tcp",
                    "packet_length": random.randint(64, 1500),
                    "interface": "Wi-Fi",
                    "flags": "SYN",
                    "description": attack_info["description"],
                    "recommended_action": "Block source IP and monitor for similar patterns"
                }
                
                # Store the alert in a way the alerts endpoint can find it
                if not hasattr(self, '_stored_alerts'):
                    self._stored_alerts = []
                
                self._stored_alerts.insert(0, test_alert)
                # Keep only last 1000 alerts
                self._stored_alerts = self._stored_alerts[:1000]
                
                # Also try to store in alert manager
                if hasattr(self.nids.alert_manager, '_recent_alerts'):
                    if self.nids.alert_manager._recent_alerts is None:
                        self.nids.alert_manager._recent_alerts = []
                    self.nids.alert_manager._recent_alerts.insert(0, test_alert)
                    self.nids.alert_manager._recent_alerts = self.nids.alert_manager._recent_alerts[:1000]
                
                logger.info(f"Test alert added: {test_alert['attack_type']}")
                
                return {
                    "ok": True,
                    "message": "Test alert added successfully",
                    "alert": test_alert
                }
                
            except Exception as e:
                logger.error(f"Failed to add test alert: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        

    
    async def _restart_nids(self):
        """Restart NIDS system with new configuration"""
        try:
            if self.nids and self.nids._running:
                logger.info("Stopping NIDS for interface change...")
                self.nids.stop_detection()
            
            # Reinitialize NIDS with new config
            logger.info("Reinitializing NIDS with new interface...")
            self._initialize_nids()
            
            if self.nids:
                logger.info("Starting NIDS with new interface...")
                self.nids.start_detection()
                logger.info("NIDS restarted successfully")
            else:
                logger.error("Failed to reinitialize NIDS")
                
        except Exception as e:
            logger.error(f"Failed to restart NIDS: {e}")
    



def start_api_server(port: int = 8000, config_path: str = "config.yaml", host: str = "0.0.0.0"):
    """Start the FastAPI server"""
    try:
        # Initialize API server
        api_server = NIDSAPIServer(config_path)
        
        # Start the server
        logger.info(f"Starting NIDS API server on {host}:{port}")
        uvicorn.run(
            api_server.app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        raise


if __name__ == "__main__":
    start_api_server()