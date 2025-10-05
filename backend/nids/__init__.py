"""
Real-Time Network Intrusion Detection System

A modular Python pipeline for real-time network intrusion detection
using MATLAB-trained models.
"""

from .core import RealTimeNIDS
from .capture import PacketCapture
from .features import FeatureExtractor
from .models import ModelAdapter
from .alerts import AlertManager

__version__ = "1.0.0"
__all__ = [
    "RealTimeNIDS",
    "PacketCapture", 
    "FeatureExtractor",
    "ModelAdapter",
    "AlertManager"
]