"""
Spider-Verse Theme for NIDS PyQt6 Frontend
Dark theme with neon accents and glitch effects
"""

import random
from typing import List
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor


class SpiderTheme:
    """
    Spider-Verse inspired theme with dark backgrounds and neon accents
    """
    
    def __init__(self):
        # Base colors
        self.primary_bg = "#1a1a2e"
        self.secondary_bg = "#16213e"
        self.tertiary_bg = "#0f3460"
        self.accent_red = "#e94560"
        self.accent_blue = "#3498db"
        self.accent_green = "#00ff88"
        self.text_primary = "#ffffff"
        self.text_secondary = "#b0b0b0"
        self.text_muted = "#888888"
        
        # Glitch colors for effects
        self.glitch_colors = [
            "#ff0080", "#00ff80", "#8000ff", 
            "#ff8000", "#0080ff", "#ff4080"
        ]
        
        self.current_glitch_color = self.accent_red
    
    def get_main_stylesheet(self) -> str:
        """Get main application stylesheet"""
        return f"""
            QMainWindow {{
                background-color: {self.primary_bg};
                color: {self.text_primary};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            QWidget {{
                background-color: transparent;
                color: {self.text_primary};
            }}
            
            QFrame {{
                border: none;
                background-color: transparent;
            }}
            
            QSplitter::handle {{
                background-color: {self.accent_blue};
                width: 3px;
                height: 3px;
            }}
            
            QSplitter::handle:hover {{
                background-color: {self.accent_red};
            }}
            
            QScrollBar:vertical {{
                background-color: {self.secondary_bg};
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.accent_blue};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.accent_red};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background-color: {self.secondary_bg};
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {self.accent_blue};
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {self.accent_red};
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
            }}
        """
    
    def get_tab_stylesheet(self) -> str:
        """Get tab widget stylesheet"""
        return f"""
            QTabWidget::pane {{
                border: 2px solid {self.accent_blue};
                border-radius: 8px;
                background-color: {self.primary_bg};
                margin-top: -1px;
            }}
            
            QTabBar::tab {{
                background-color: {self.secondary_bg};
                color: {self.text_secondary};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.accent_red};
                color: {self.text_primary};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {self.tertiary_bg};
                color: {self.text_primary};
            }}
        """
    
    def get_button_stylesheet(self) -> str:
        """Get button stylesheet"""
        return f"""
            QPushButton {{
                background-color: {self.accent_red};
                color: {self.text_primary};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }}
            
            QPushButton:hover {{
                background-color: #c73650;
                transform: translateY(-1px);
            }}
            
            QPushButton:pressed {{
                background-color: #a02d42;
                transform: translateY(1px);
            }}
            
            QPushButton:disabled {{
                background-color: {self.text_muted};
                color: {self.text_secondary};
            }}
        """
    
    def get_input_stylesheet(self) -> str:
        """Get input field stylesheet"""
        return f"""
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {self.secondary_bg};
                color: {self.text_primary};
                border: 2px solid {self.accent_blue};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                selection-background-color: {self.accent_red};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {self.accent_green};
                background-color: {self.primary_bg};
            }}
            
            QComboBox {{
                background-color: {self.secondary_bg};
                color: {self.text_primary};
                border: 2px solid {self.accent_blue};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Courier New', monospace;
            }}
            
            QComboBox:focus {{
                border-color: {self.accent_green};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.accent_blue};
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.secondary_bg};
                color: {self.text_primary};
                border: 1px solid {self.accent_blue};
                selection-background-color: {self.accent_red};
            }}
        """
    
    def get_table_stylesheet(self) -> str:
        """Get table stylesheet"""
        return f"""
            QTableWidget {{
                background-color: {self.primary_bg};
                alternate-background-color: {self.secondary_bg};
                color: {self.text_primary};
                gridline-color: {self.accent_blue};
                border: 2px solid {self.accent_blue};
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }}
            
            QTableWidget::item {{
                padding: 6px;
                border: none;
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.accent_red};
                color: {self.text_primary};
            }}
            
            QHeaderView::section {{
                background-color: {self.tertiary_bg};
                color: {self.text_primary};
                padding: 10px;
                border: 1px solid {self.accent_blue};
                font-weight: bold;
                font-size: 11px;
            }}
            
            QHeaderView::section:hover {{
                background-color: {self.accent_red};
            }}
        """
    
    def apply_glitch_effect(self):
        """Apply random glitch color effect"""
        self.current_glitch_color = random.choice(self.glitch_colors)
    
    def get_glitch_color(self) -> str:
        """Get current glitch color"""
        return self.current_glitch_color
    
    def get_status_colors(self) -> dict:
        """Get status indicator colors"""
        return {
            "healthy": "#2ecc71",    # Green
            "warning": "#f1c40f",    # Yellow
            "error": "#e74c3c",      # Red
            "unknown": "#95a5a6"     # Gray
        }
    
    def get_severity_colors(self) -> dict:
        """Get alert severity colors"""
        return {
            "critical": "#e74c3c",   # Red
            "high": "#f39c12",       # Orange
            "medium": "#3498db",     # Blue
            "low": "#95a5a6",        # Gray
            "info": "#1abc9c"        # Teal
        }