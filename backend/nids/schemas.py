"""
Type definitions and data schemas for the NIDS pipeline.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np


class PacketInfo(BaseModel):
    """Raw packet information from capture layer."""
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str  # 'tcp', 'udp', 'icmp'
    packet_size: int
    payload_size: int
    payload: Optional[bytes] = None
    
    # TCP-specific fields
    tcp_flags: Optional[int] = None
    tcp_window: Optional[int] = None
    tcp_seq: Optional[int] = None
    tcp_ack: Optional[int] = None
    
    # IP-specific fields
    ttl: Optional[int] = None
    ip_flags: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True


class FlowKey(BaseModel):
    """5-tuple flow identifier."""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    
    def __hash__(self):
        return hash((self.src_ip, self.dst_ip, self.src_port, self.dst_port, self.protocol))
    
    def __eq__(self, other):
        if not isinstance(other, FlowKey):
            return False
        return (self.src_ip, self.dst_ip, self.src_port, self.dst_port, self.protocol) == \
               (other.src_ip, other.dst_ip, other.src_port, other.dst_port, other.protocol)


class FlowState(BaseModel):
    """Flow session state tracking."""
    flow_key: FlowKey
    start_time: float
    last_seen: float
    
    # Packet counts
    src_packets: int = 0
    dst_packets: int = 0
    
    # Byte counts
    src_bytes: int = 0
    dst_bytes: int = 0
    
    # TCP state tracking
    syn_count: int = 0
    fin_count: int = 0
    rst_count: int = 0
    
    # Timing statistics
    inter_arrival_times: List[float] = Field(default_factory=list)
    packet_sizes: List[int] = Field(default_factory=list)
    
    # Window tracking for sliding features
    recent_packets: List[PacketInfo] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class FeatureVector(BaseModel):
    """Extracted features for model input."""
    timestamp: float
    flow_key: FlowKey
    
    # Packet-level features
    packet_size: float
    direction: int  # 0=src->dst, 1=dst->src
    inter_arrival_delta: float
    tcp_flags_bitmap: int
    ttl: float
    
    # Flow-level features
    total_bytes: float
    total_packets: float
    bytes_ratio: float
    packets_per_second: float
    syn_fin_ratio: float
    
    # Window-based features
    size_mean: float
    size_std: float
    iat_mean: float
    iat_std: float
    burstiness: float
    
    # Payload features
    payload_entropy: float
    printable_ratio: float
    dns_qname_length: Optional[float] = None
    tls_sni_present: Optional[bool] = None
    
    def to_array(self, feature_order: List[str]) -> np.ndarray:
        """Convert to numpy array in specified feature order."""
        feature_dict = self.dict()
        return np.array([feature_dict.get(name, 0.0) for name in feature_order])
    
    class Config:
        arbitrary_types_allowed = True


class ModelPrediction(BaseModel):
    """Model prediction result."""
    timestamp: float
    flow_key: FlowKey
    
    # Binary classification
    is_attack: bool
    attack_probability: float
    
    # Multi-class classification (if triggered)
    attack_class: Optional[str] = None
    class_probabilities: Optional[Dict[str, float]] = None
    
    # Model metadata
    model_version: str
    threshold_used: float
    processing_time_ms: float


class Alert(BaseModel):
    """Security alert."""
    timestamp: float
    alert_id: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    
    # Attack details
    attack_type: str
    confidence: float
    source_ip: str
    destination_ip: str
    
    # Context
    flow_key: FlowKey
    prediction: ModelPrediction
    
    # Alert metadata
    description: str
    recommended_action: Optional[str] = None


class ProcessingStats(BaseModel):
    """Performance and processing statistics."""
    timestamp: float
    
    # Throughput metrics
    packets_processed: int
    packets_per_second: float
    
    # Latency metrics (milliseconds)
    avg_packet_latency: float
    p95_packet_latency: float
    avg_multiclass_latency: Optional[float] = None
    
    # Resource usage
    active_flows: int
    memory_usage_mb: float
    cpu_usage_percent: float
    
    # Detection metrics
    alerts_generated: int
    false_positive_rate: Optional[float] = None
    detection_rate: Optional[float] = None