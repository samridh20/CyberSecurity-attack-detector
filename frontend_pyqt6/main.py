#!/usr/bin/env python3
"""
NIDS PyQt6 Frontend - Spider-Verse themed desktop monitor
Real-time network intrusion detection system UI
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from loguru import logger

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import NIDSMainWindow
from core.config_manager import ConfigManager
from core.api_client import NIDSAPIClient


def setup_logging():
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | {message}"
    )
    logger.add(
        "logs/nids_ui.log",
        rotation="10 MB",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
    )


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger.info("Starting NIDS PyQt6 Frontend")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("NIDS Monitor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NIDS")
    
    # Set application properties
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    try:
        # Initialize configuration manager
        config_manager = ConfigManager()
        
        # Initialize API client
        api_client = NIDSAPIClient()
        
        # Create main window
        main_window = NIDSMainWindow(config_manager, api_client)
        main_window.show()
        
        logger.info("NIDS UI started successfully")
        
        # Run application
        return app.exec()
        
    except Exception as e:
        logger.error(f"Failed to start NIDS UI: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())