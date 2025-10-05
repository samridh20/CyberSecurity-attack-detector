"""
Charts Widget - Real-time data visualization
Shows network traffic and alert trends using pyqtgraph
"""

import time
from collections import deque
from typing import Dict, Any, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from loguru import logger


class RealTimeChart(QFrame):
    """Real-time line chart widget"""
    
    def __init__(self, title: str, y_label: str, max_points: int = 300, parent=None):
        super().__init__(parent)
        self.title = title
        self.max_points = max_points
        self.data_x = deque(maxlen=max_points)
        self.data_y = deque(maxlen=max_points)
        
        self._setup_ui(y_label)
        self._apply_styling()
    
    def _setup_ui(self, y_label: str):
        """Setup chart UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setObjectName("chart_title")
        layout.addWidget(title_label)
        
        # Chart
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1a1a2e')
        self.plot_widget.setLabel('left', y_label, color='#ffffff')
        self.plot_widget.setLabel('bottom', 'Time', color='#ffffff')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Configure plot
        self.plot_widget.getAxis('left').setPen(color='#ffffff')
        self.plot_widget.getAxis('bottom').setPen(color='#ffffff')
        self.plot_widget.getAxis('left').setTextPen(color='#ffffff')
        self.plot_widget.getAxis('bottom').setTextPen(color='#ffffff')
        
        # Create plot line
        self.plot_line = self.plot_widget.plot(
            pen=pg.mkPen(color='#00ff88', width=2),
            symbol='o',
            symbolSize=4,
            symbolBrush='#00ff88'
        )
        
        layout.addWidget(self.plot_widget)
    
    def _apply_styling(self):
        """Apply chart styling"""
        self.setStyleSheet("""
            RealTimeChart {
                background-color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin: 5px;
            }
            
            QLabel#chart_title {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 5px;
                text-align: center;
            }
        """)
    
    def add_data_point(self, value: float):
        """Add new data point"""
        current_time = time.time()
        
        self.data_x.append(current_time)
        self.data_y.append(value)
        
        # Update plot
        if len(self.data_x) > 1:
            # Convert to relative time (seconds ago)
            relative_times = [t - current_time for t in self.data_x]
            self.plot_line.setData(relative_times, list(self.data_y))
    
    def clear_data(self):
        """Clear all data points"""
        self.data_x.clear()
        self.data_y.clear()
        self.plot_line.setData([], [])


class AlertsHistogram(QFrame):
    """Histogram showing alert distribution by type"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.alert_counts = {}
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup histogram UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("Alert Distribution")
        title_label.setObjectName("chart_title")
        layout.addWidget(title_label)
        
        # Bar chart
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1a1a2e')
        self.plot_widget.setLabel('left', 'Count', color='#ffffff')
        self.plot_widget.setLabel('bottom', 'Alert Type', color='#ffffff')
        self.plot_widget.showGrid(x=False, y=True, alpha=0.3)
        
        # Configure plot
        self.plot_widget.getAxis('left').setPen(color='#ffffff')
        self.plot_widget.getAxis('bottom').setPen(color='#ffffff')
        self.plot_widget.getAxis('left').setTextPen(color='#ffffff')
        self.plot_widget.getAxis('bottom').setTextPen(color='#ffffff')
        
        layout.addWidget(self.plot_widget)
    
    def _apply_styling(self):
        """Apply histogram styling"""
        self.setStyleSheet("""
            AlertsHistogram {
                background-color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin: 5px;
            }
            
            QLabel#chart_title {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 5px;
                text-align: center;
            }
        """)
    
    def update_alert_counts(self, alert_types: Dict[str, int]):
        """Update alert type counts"""
        self.alert_counts = alert_types
        self._redraw_histogram()
    
    def _redraw_histogram(self):
        """Redraw the histogram"""
        self.plot_widget.clear()
        
        if not self.alert_counts:
            return
        
        # Prepare data
        types = list(self.alert_counts.keys())
        counts = list(self.alert_counts.values())
        
        if not types:
            return
        
        # Create bar chart
        x_pos = list(range(len(types)))
        
        # Create bars
        bar_item = pg.BarGraphItem(
            x=x_pos,
            height=counts,
            width=0.8,
            brush='#e94560',
            pen=pg.mkPen(color='#ffffff', width=1)
        )
        
        self.plot_widget.addItem(bar_item)
        
        # Set x-axis labels
        x_axis = self.plot_widget.getAxis('bottom')
        x_axis.setTicks([[(i, types[i]) for i in range(len(types))]])


class ChartsWidget(QWidget):
    """
    Charts widget showing real-time network and security metrics
    """
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        
        self._setup_ui()
        self._apply_styling()
        self._setup_timers()
    
    def _setup_ui(self):
        """Setup charts UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Top row - Traffic charts
        top_layout = QHBoxLayout()
        
        # Packets per second chart
        self.pps_chart = RealTimeChart("Packets per Second", "PPS")
        top_layout.addWidget(self.pps_chart)
        
        # Alerts per second chart
        self.aps_chart = RealTimeChart("Alerts per Second", "APS")
        top_layout.addWidget(self.aps_chart)
        
        layout.addLayout(top_layout)
        
        # Bottom row - Alert distribution
        self.alerts_histogram = AlertsHistogram()
        layout.addWidget(self.alerts_histogram)
        
        # Set proportions
        layout.setStretch(0, 2)  # Top charts
        layout.setStretch(1, 1)  # Bottom histogram
    
    def _apply_styling(self):
        """Apply widget styling"""
        self.setStyleSheet("""
            ChartsWidget {
                background-color: #1a1a2e;
                border-radius: 10px;
                padding: 5px;
            }
        """)
    
    def _setup_timers(self):
        """Setup update timers"""
        # Chart update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_histogram)
        self.update_timer.start(10000)  # Update histogram every 10 seconds
    
    def update_charts(self, stats_data: Dict[str, Any]):
        """Update charts with new statistics"""
        try:
            # Update PPS chart
            pps = stats_data.get('pps', 0)
            self.pps_chart.add_data_point(pps)
            
            # Update APS chart
            aps = stats_data.get('alerts_per_sec', 0)
            self.aps_chart.add_data_point(aps)
            
            logger.debug(f"Charts updated: {pps} pps, {aps} aps")
            
        except Exception as e:
            logger.error(f"Failed to update charts: {e}")
    
    def _update_histogram(self):
        """Update alert distribution histogram"""
        try:
            # Get recent alerts from API
            alerts = self.api_client.get_recent_alerts(100)
            if not alerts:
                return
            
            # Count alert types
            alert_counts = {}
            for alert in alerts:
                alert_type = alert.get('attack_type', 'Unknown')
                alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
            
            # Update histogram
            self.alerts_histogram.update_alert_counts(alert_counts)
            
        except Exception as e:
            logger.debug(f"Failed to update histogram: {e}")
    
    def clear_charts(self):
        """Clear all chart data"""
        self.pps_chart.clear_data()
        self.aps_chart.clear_data()
        self.alerts_histogram.update_alert_counts({})
        logger.info("Charts cleared")