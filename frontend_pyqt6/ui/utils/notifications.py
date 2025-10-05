"""
Notification Manager for Windows Toast Notifications
Handles success, error, and info notifications
"""

import sys
from typing import Optional
from loguru import logger

# Windows toast notification imports
try:
    if sys.platform == "win32":
        try:
            # Try winrt first (preferred)
            from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification
            from winrt.windows.data.xml.dom import XmlDocument
            WINRT_AVAILABLE = True
            WIN10TOAST_AVAILABLE = False
        except ImportError:
            # Fallback to win10toast
            try:
                from win10toast import ToastNotifier
                WINRT_AVAILABLE = False
                WIN10TOAST_AVAILABLE = True
            except ImportError:
                WINRT_AVAILABLE = False
                WIN10TOAST_AVAILABLE = False
    else:
        WINRT_AVAILABLE = False
        WIN10TOAST_AVAILABLE = False
except ImportError:
    WINRT_AVAILABLE = False
    WIN10TOAST_AVAILABLE = False


class NotificationManager:
    """
    Manages Windows toast notifications for the NIDS UI
    """
    
    def __init__(self):
        self.enabled = WINRT_AVAILABLE or WIN10TOAST_AVAILABLE
        self.notifier = None
        
        if self.enabled:
            self._initialize_notifier()
        else:
            logger.warning("Toast notifications not available on this platform")
    
    def _initialize_notifier(self):
        """Initialize the notification system"""
        try:
            if WINRT_AVAILABLE:
                self.notifier = ToastNotificationManager.create_toast_notifier("NIDS Monitor")
                logger.info("Using WinRT for toast notifications")
            elif WIN10TOAST_AVAILABLE:
                self.notifier = ToastNotifier()
                logger.info("Using win10toast for notifications")
        except Exception as e:
            logger.error(f"Failed to initialize notifications: {e}")
            self.enabled = False
    
    def show_success(self, title: str, message: str, duration: int = 3):
        """Show success notification"""
        if not self.enabled:
            logger.info(f"SUCCESS: {title} - {message}")
            return
        
        try:
            if WINRT_AVAILABLE:
                self._show_winrt_toast(title, message, "success", duration)
            elif WIN10TOAST_AVAILABLE:
                self.notifier.show_toast(
                    title=f"✅ {title}",
                    msg=message,
                    duration=duration,
                    threaded=True
                )
        except Exception as e:
            logger.error(f"Failed to show success notification: {e}")
    
    def show_error(self, title: str, message: str, duration: int = 5):
        """Show error notification"""
        if not self.enabled:
            logger.error(f"ERROR: {title} - {message}")
            return
        
        try:
            if WINRT_AVAILABLE:
                self._show_winrt_toast(title, message, "error", duration)
            elif WIN10TOAST_AVAILABLE:
                self.notifier.show_toast(
                    title=f"❌ {title}",
                    msg=message,
                    duration=duration,
                    threaded=True
                )
        except Exception as e:
            logger.error(f"Failed to show error notification: {e}")
    
    def show_warning(self, title: str, message: str, duration: int = 4):
        """Show warning notification"""
        if not self.enabled:
            logger.warning(f"WARNING: {title} - {message}")
            return
        
        try:
            if WINRT_AVAILABLE:
                self._show_winrt_toast(title, message, "warning", duration)
            elif WIN10TOAST_AVAILABLE:
                self.notifier.show_toast(
                    title=f"⚠️ {title}",
                    msg=message,
                    duration=duration,
                    threaded=True
                )
        except Exception as e:
            logger.error(f"Failed to show warning notification: {e}")
    
    def show_info(self, title: str, message: str, duration: int = 3):
        """Show info notification"""
        if not self.enabled:
            logger.info(f"INFO: {title} - {message}")
            return
        
        try:
            if WINRT_AVAILABLE:
                self._show_winrt_toast(title, message, "info", duration)
            elif WIN10TOAST_AVAILABLE:
                self.notifier.show_toast(
                    title=f"ℹ️ {title}",
                    msg=message,
                    duration=duration,
                    threaded=True
                )
        except Exception as e:
            logger.error(f"Failed to show info notification: {e}")
    
    def _show_winrt_toast(self, title: str, message: str, notification_type: str, duration: int):
        """Show toast using WinRT"""
        try:
            # Choose icon based on type
            icon_map = {
                "success": "✅",
                "error": "❌", 
                "warning": "⚠️",
                "info": "ℹ️"
            }
            
            icon = icon_map.get(notification_type, "ℹ️")
            
            # Create toast XML
            toast_xml = f"""
            <toast duration="{'long' if duration > 4 else 'short'}">
                <visual>
                    <binding template="ToastGeneric">
                        <text>{icon} {title}</text>
                        <text>{message}</text>
                    </binding>
                </visual>
                <audio src="ms-winsoundevent:Notification.Default" />
            </toast>
            """
            
            # Create and show toast
            xml_doc = XmlDocument()
            xml_doc.load_xml(toast_xml)
            toast = ToastNotification(xml_doc)
            self.notifier.show(toast)
            
        except Exception as e:
            logger.error(f"Failed to show WinRT toast: {e}")
    
    def is_available(self) -> bool:
        """Check if notifications are available"""
        return self.enabled