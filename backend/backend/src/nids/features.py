"""
Feature extraction module for network intrusion detection.
Implements sessionization, sliding windows, and comprehensive feature engineering.
"""

import time
import math
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
import numpy as np
from loguru import logger

try:
    from numba import jit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # Create dummy decorator
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .schemas import PacketInfo, FlowKey, FlowState, FeatureVector


class FeatureExtractor:
    """
    Extracts features from network packets for ML model input.
    Handles sessionization, sliding windows, and feature engineering.
    """
    
    def __init__(self, 
                 window_size: int = 10,
                 window_overlap: float = 0.5,
                 session_timeout: float = 300.0,
                 max_payload_bytes: int = 1500,
                 use_numba: bool = True):
        """
        Initialize feature extractor.
        
        Args:
            window_size: Number of packets in sliding window
            window_overlap: Window overlap ratio (0.0-1.0)
            session_timeout: Session timeout in seconds
            max_payload_bytes: Maximum payload bytes to analyze
            use_numba: Use Numba optimization if available
        """
        self.window_size = window_size
        self.window_overlap = window_overlap
        self.session_timeout = session_timeout
        self.max_payload_bytes = max_payload_bytes
        self.use_numba = use_numba and NUMBA_AVAILABLE
        
        # Flow tracking
        self.flows: Dict[FlowKey, FlowState] = {}
        self.last_cleanup = time.time()
        
        logger.info(f"Feature extractor initialized (numba={'enabled' if self.use_numba else 'disabled'})")
    
    def _create_flow_key(self, packet: PacketInfo) -> FlowKey:
        """Create flow key from packet."""
        return FlowKey(
            src_ip=packet.src_ip,
            dst_ip=packet.dst_ip,
            src_port=packet.src_port,
            dst_port=packet.dst_port,
            protocol=packet.protocol
        )
    
    def _get_or_create_flow(self, packet: PacketInfo) -> FlowState:
        """Get existing flow or create new one."""
        flow_key = self._create_flow_key(packet)
        
        if flow_key not in self.flows:
            self.flows[flow_key] = FlowState(
                flow_key=flow_key,
                start_time=packet.timestamp,
                last_seen=packet.timestamp
            )
        
        return self.flows[flow_key]
    
    def _update_flow_state(self, flow: FlowState, packet: PacketInfo):
        """Update flow state with new packet."""
        flow.last_seen = packet.timestamp
        
        # Determine direction (0=src->dst, 1=dst->src)
        if (packet.src_ip == flow.flow_key.src_ip and 
            packet.src_port == flow.flow_key.src_port):
            # Forward direction
            flow.src_packets += 1
            flow.src_bytes += packet.packet_size
        else:
            # Reverse direction
            flow.dst_packets += 1
            flow.dst_bytes += packet.packet_size
        
        # TCP flag tracking
        if packet.tcp_flags is not None:
            if packet.tcp_flags & 0x02:  # SYN
                flow.syn_count += 1
            if packet.tcp_flags & 0x01:  # FIN
                flow.fin_count += 1
            if packet.tcp_flags & 0x04:  # RST
                flow.rst_count += 1
        
        # Update timing statistics
        if flow.recent_packets:
            last_time = flow.recent_packets[-1].timestamp
            iat = packet.timestamp - last_time
            flow.inter_arrival_times.append(iat)
        
        flow.packet_sizes.append(packet.packet_size)
        flow.recent_packets.append(packet)
        
        # Maintain sliding window
        if len(flow.recent_packets) > self.window_size:
            flow.recent_packets.pop(0)
            flow.inter_arrival_times = flow.inter_arrival_times[-self.window_size:]
            flow.packet_sizes = flow.packet_sizes[-self.window_size:]
    
    def _cleanup_expired_flows(self):
        """Remove expired flows to prevent memory leaks."""
        current_time = time.time()
        
        # Only cleanup every 60 seconds
        if current_time - self.last_cleanup < 60:
            return
        
        expired_flows = []
        for flow_key, flow in self.flows.items():
            if current_time - flow.last_seen > self.session_timeout:
                expired_flows.append(flow_key)
        
        for flow_key in expired_flows:
            del self.flows[flow_key]
        
        if expired_flows:
            logger.debug(f"Cleaned up {len(expired_flows)} expired flows")
        
        self.last_cleanup = current_time
    
    #@jit(nopython=True) if NUMBA_AVAILABLE else lambda x: x
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of byte data."""
        if not data:
            return 0.0
        
        # Count byte frequencies
        counts = np.zeros(256, dtype=np.int32)
        for byte in data:
            counts[byte] += 1
        
        # Calculate entropy
        entropy = 0.0
        length = len(data)
        for count in counts:
            if count > 0:
                p = count / length
                entropy -= p * math.log2(p)
        
        return entropy
    
    def _extract_payload_features(self, packet: PacketInfo) -> Dict[str, float]:
        """Extract payload-based features."""
        features = {
            'payload_entropy': 0.0,
            'printable_ratio': 0.0,
            'dns_qname_length': None,
            'tls_sni_present': None
        }
        
        if not packet.payload or len(packet.payload) == 0:
            return features
        
        # Limit payload analysis
        payload = packet.payload[:self.max_payload_bytes]
        
        # Calculate entropy
        features['payload_entropy'] = self._calculate_entropy(payload)
        
        # Calculate printable character ratio
        printable_count = sum(1 for b in payload if 32 <= b <= 126)
        features['printable_ratio'] = printable_count / len(payload)
        
        # DNS-specific features
        if packet.protocol == 'udp' and packet.dst_port == 53:
            # Simple DNS QNAME length estimation
            # This is a heuristic - proper DNS parsing would be more accurate
            if len(payload) > 12:  # DNS header is 12 bytes
                qname_section = payload[12:]
                qname_length = 0
                i = 0
                while i < len(qname_section) and qname_section[i] != 0:
                    label_length = qname_section[i]
                    if label_length > 63:  # Invalid label length
                        break
                    qname_length += label_length + 1
                    i += label_length + 1
                    if i >= len(qname_section):
                        break
                features['dns_qname_length'] = float(qname_length)
        
        # TLS SNI detection (simplified)
        if packet.protocol == 'tcp' and packet.dst_port == 443:
            # Look for TLS Client Hello with SNI
            # This is a very basic heuristic
            if len(payload) > 50 and payload[0] == 0x16:  # TLS Handshake
                features['tls_sni_present'] = b'\\x00\\x00' in payload  # SNI extension marker
        
        return features
    
    def _calculate_window_features(self, flow: FlowState) -> Dict[str, float]:
        """Calculate sliding window statistical features."""
        features = {
            'size_mean': 0.0,
            'size_std': 0.0,
            'iat_mean': 0.0,
            'iat_std': 0.0,
            'burstiness': 0.0
        }
        
        if not flow.packet_sizes:
            return features
        
        # Packet size statistics
        sizes = np.array(flow.packet_sizes)
        features['size_mean'] = float(np.mean(sizes))
        features['size_std'] = float(np.std(sizes)) if len(sizes) > 1 else 0.0
        
        # Inter-arrival time statistics
        if flow.inter_arrival_times:
            iats = np.array(flow.inter_arrival_times)
            features['iat_mean'] = float(np.mean(iats))
            features['iat_std'] = float(np.std(iats)) if len(iats) > 1 else 0.0
            
            # Burstiness metric (coefficient of variation)
            if features['iat_mean'] > 0:
                features['burstiness'] = features['iat_std'] / features['iat_mean']
        
        return features
    
    def extract_features(self, packet: PacketInfo) -> FeatureVector:
        """
        Extract comprehensive features from packet.
        
        Args:
            packet: Input packet information
            
        Returns:
            FeatureVector with extracted features
        """
        # Update flow state
        flow = self._get_or_create_flow(packet)
        self._update_flow_state(flow, packet)
        
        # Determine packet direction
        direction = 0 if (packet.src_ip == flow.flow_key.src_ip and 
                         packet.src_port == flow.flow_key.src_port) else 1
        
        # Calculate inter-arrival delta
        inter_arrival_delta = 0.0
        if len(flow.recent_packets) > 1:
            inter_arrival_delta = packet.timestamp - flow.recent_packets[-2].timestamp
        
        # Basic packet features
        tcp_flags_bitmap = packet.tcp_flags if packet.tcp_flags is not None else 0
        ttl = float(packet.ttl) if packet.ttl is not None else 64.0
        
        # Flow-level features
        total_bytes = float(flow.src_bytes + flow.dst_bytes)
        total_packets = float(flow.src_packets + flow.dst_packets)
        
        # Avoid division by zero
        bytes_ratio = (flow.src_bytes / max(flow.dst_bytes, 1)) if flow.dst_bytes > 0 else 0.0
        
        # Calculate packets per second
        flow_duration = packet.timestamp - flow.start_time
        packets_per_second = total_packets / max(flow_duration, 0.001)
        
        # TCP flag ratios
        syn_fin_ratio = 0.0
        if flow.fin_count > 0:
            syn_fin_ratio = flow.syn_count / flow.fin_count
        elif flow.syn_count > 0:
            syn_fin_ratio = float(flow.syn_count)
        
        # Window-based statistical features
        window_features = self._calculate_window_features(flow)
        
        # Payload features
        payload_features = self._extract_payload_features(packet)
        
        # Cleanup expired flows periodically
        self._cleanup_expired_flows()
        
        return FeatureVector(
            timestamp=packet.timestamp,
            flow_key=flow.flow_key,
            
            # Packet-level features
            packet_size=float(packet.packet_size),
            direction=direction,
            inter_arrival_delta=inter_arrival_delta,
            tcp_flags_bitmap=tcp_flags_bitmap,
            ttl=ttl,
            
            # Flow-level features
            total_bytes=total_bytes,
            total_packets=total_packets,
            bytes_ratio=bytes_ratio,
            packets_per_second=packets_per_second,
            syn_fin_ratio=syn_fin_ratio,
            
            # Window-based features
            size_mean=window_features['size_mean'],
            size_std=window_features['size_std'],
            iat_mean=window_features['iat_mean'],
            iat_std=window_features['iat_std'],
            burstiness=window_features['burstiness'],
            
            # Payload features
            payload_entropy=payload_features['payload_entropy'],
            printable_ratio=payload_features['printable_ratio'],
            dns_qname_length=payload_features['dns_qname_length'],
            tls_sni_present=payload_features['tls_sni_present']
        )
    
    def get_flow_count(self) -> int:
        """Get current number of active flows."""
        return len(self.flows)
    
    def reset(self):
        """Reset all flow state (useful for testing)."""
        self.flows.clear()
        logger.info("Feature extractor state reset")