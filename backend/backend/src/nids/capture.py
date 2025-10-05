"""
Network packet capture module using Scapy + Npcap.
Handles L2-L4 parsing with graceful fallbacks.
"""

import time
from typing import Iterator, Optional, Callable
from threading import Thread, Event
import queue
from loguru import logger

try:
    from scapy.all import (
        sniff, get_if_list, conf, 
        Ether, IP, IPv6, TCP, UDP, ICMP,
        Raw, DNS
    )
    # ✅ TLS is no longer in scapy.all in newer versions
    from scapy.layers.tls.all import TLS
except ImportError:
    logger.error("Scapy not installed or TLS layer missing. Run: pip install scapy")
    raise

from .schemas import PacketInfo


class PacketCapture:
    """
    Real-time packet capture using Scapy with Npcap backend.
    Provides parsed packet information with graceful error handling.
    """
    
    def __init__(self, 
                 interface: Optional[str] = None,
                 bpf_filter: str = "tcp or udp",
                 promiscuous: bool = False,
                 buffer_size: int = 2048,
                 timeout: float = 1.0):
        """
        Initialize packet capture.
        
        Args:
            interface: Network interface name (None = auto-detect)
            bpf_filter: Berkeley Packet Filter expression
            promiscuous: Enable promiscuous mode
            buffer_size: Capture buffer size
            timeout: Capture timeout in seconds
        """
        self.interface = interface or self._auto_detect_interface()
        self.bpf_filter = bpf_filter
        self.promiscuous = promiscuous
        self.buffer_size = buffer_size
        self.timeout = timeout
        
        self._stop_event = Event()
        self._packet_queue = queue.Queue(maxsize=10000)
        self._capture_thread: Optional[Thread] = None
        
        logger.info(f"Initialized packet capture on interface: {self.interface}")
    
    def _auto_detect_interface(self) -> str:
        """Auto-detect the best network interface."""
        interfaces = get_if_list()
        
        # Prefer Ethernet interfaces
        for iface in interfaces:
            if any(keyword in iface.lower() for keyword in ['ethernet', 'local area connection']):
                logger.info(f"Auto-detected interface: {iface}")
                return iface
        
        # Fallback to first available
        if interfaces:
            logger.info(f"Using first available interface: {interfaces[0]}")
            return interfaces[0]
        
        raise RuntimeError("No network interfaces found")
    
    def _parse_packet(self, packet) -> Optional[PacketInfo]:
        """
        Parse raw packet into structured PacketInfo.
        Handles missing fields gracefully.
        """
        try:
            timestamp = time.time()
            
            # Extract IP layer (IPv4 or IPv6)
            ip_layer = None
            if packet.haslayer(IP):
                ip_layer = packet[IP]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                ttl = ip_layer.ttl
                ip_flags = ip_layer.flags
            elif packet.haslayer(IPv6):
                ip_layer = packet[IPv6]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                ttl = ip_layer.hlim  # Hop limit in IPv6
                ip_flags = 0
            else:
                # No IP layer found
                return None
            
            # Extract transport layer
            protocol = "unknown"
            src_port = dst_port = 0
            tcp_flags = tcp_window = tcp_seq = tcp_ack = None
            
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                protocol = "tcp"
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                tcp_flags = tcp_layer.flags
                tcp_window = tcp_layer.window
                tcp_seq = tcp_layer.seq
                tcp_ack = tcp_layer.ack
                
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                protocol = "udp"
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
                
            elif packet.haslayer(ICMP):
                protocol = "icmp"
                # ICMP doesn't have ports
                src_port = dst_port = 0
            
            # Extract payload
            payload = None
            payload_size = 0
            if packet.haslayer(Raw):
                payload = bytes(packet[Raw])
                payload_size = len(payload)
            
            # Calculate packet size
            packet_size = len(packet)
            
            return PacketInfo(
                timestamp=timestamp,
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol,
                packet_size=packet_size,
                payload_size=payload_size,
                payload=payload,
                tcp_flags=tcp_flags,
                tcp_window=tcp_window,
                tcp_seq=tcp_seq,
                tcp_ack=tcp_ack,
                ttl=ttl,
                ip_flags=ip_flags
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse packet: {e}")
            return None
    
    def _packet_handler(self, packet):
        """Handle captured packet - called by Scapy."""
        parsed = self._parse_packet(packet)
        if parsed:
            try:
                self._packet_queue.put_nowait(parsed)
            except queue.Full:
                logger.warning("Packet queue full, dropping packet")
    
    def _capture_loop(self):
        """Main capture loop running in separate thread."""
        try:
            logger.info(f"Starting packet capture on {self.interface} with filter: {self.bpf_filter}")
            
            sniff(
                iface=self.interface,
                filter=self.bpf_filter,
                prn=self._packet_handler,
                store=False,  # Don't store packets in memory
                stop_filter=lambda x: self._stop_event.is_set(),
                timeout=self.timeout
            )
            
        except Exception as e:
            logger.error(f"Capture loop error: {e}")
        finally:
            logger.info("Packet capture stopped")
    
    def start(self):
        """Start packet capture in background thread."""
        if self._capture_thread and self._capture_thread.is_alive():
            logger.warning("Capture already running")
            return
        
        self._stop_event.clear()
        self._capture_thread = Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        
        logger.info("Packet capture started")
    
    def stop(self):
        """Stop packet capture."""
        if self._capture_thread:
            self._stop_event.set()
            self._capture_thread.join(timeout=5.0)
            
        logger.info("Packet capture stopped")
    
    def get_packets(self, timeout: float = 1.0) -> Iterator[PacketInfo]:
        """
        Get captured packets as iterator.
        
        Args:
            timeout: Timeout for each packet retrieval
            
        Yields:
            PacketInfo objects
        """
        while not self._stop_event.is_set():
            try:
                packet = self._packet_queue.get(timeout=timeout)
                yield packet
            except queue.Empty:
                continue
    
    def get_packet_nowait(self) -> Optional[PacketInfo]:
        """Get a packet without blocking."""
        try:
            return self._packet_queue.get_nowait()
        except queue.Empty:
            return None
    
    @property
    def queue_size(self) -> int:
        """Current packet queue size."""
        return self._packet_queue.qsize()
    
    @property
    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._capture_thread and self._capture_thread.is_alive()


class OfflineCapture:
    """
    Offline packet capture from PCAP files for testing/evaluation.
    """
    
    def __init__(self, pcap_file: str, replay_speed: float = 1.0):
        """
        Initialize offline capture.
        
        Args:
            pcap_file: Path to PCAP file
            replay_speed: Replay speed multiplier (1.0 = real-time)
        """
        self.pcap_file = pcap_file
        self.replay_speed = replay_speed
        self._packets = []
        self._load_packets()
    
    def _load_packets(self):
        """Load packets from PCAP file."""
        try:
            from scapy.all import rdpcap
            raw_packets = rdpcap(self.pcap_file)
            
            capture = PacketCapture()  # Temporary instance for parsing
            
            for raw_packet in raw_packets:
                parsed = capture._parse_packet(raw_packet)
                if parsed:
                    self._packets.append(parsed)
            
            logger.info(f"Loaded {len(self._packets)} packets from {self.pcap_file}")
            
        except Exception as e:
            logger.error(f"Failed to load PCAP file: {e}")
            raise
    
    def replay(self) -> Iterator[PacketInfo]:
        """
        Replay packets with timing.
        
        Yields:
            PacketInfo objects with original timing
        """
        if not self._packets:
            return
        
        start_time = time.time()
        first_packet_time = self._packets[0].timestamp
        
        for packet in self._packets:
            # Calculate when this packet should be sent
            packet_offset = packet.timestamp - first_packet_time
            target_time = start_time + (packet_offset / self.replay_speed)
            
            # Wait until it's time to send this packet
            current_time = time.time()
            if current_time < target_time:
                time.sleep(target_time - current_time)
            
            yield packet