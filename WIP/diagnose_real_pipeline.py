#!/usr/bin/env python3
"""
Diagnose Real Packet Detection Pipeline
Find exactly where the real NIDS pipeline is failing
"""

import time
import sys
import threading
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path("backend").absolute()))

from nids import RealTimeNIDS
from nids.capture import PacketCapture
from nids.features import FeatureExtractor
from nids.models import SimpleModelAdapter
from nids.alerts import AlertManager
from nids.schemas import PacketInfo, FlowKey

class PipelineDiagnostic:
    """Diagnose each step of the NIDS pipeline"""
    
    def __init__(self):
        self.results = {}
    
    def test_packet_capture(self):
        """Test if packet capture is working"""
        print("1️⃣ Testing Packet Capture...")
        
        try:
            # Initialize capture
            capture = PacketCapture(
                interface=None,  # Auto-detect
                bpf_filter="tcp or udp or icmp",
                timeout=1.0
            )
            
            print(f"   📡 Interface: {capture.interface}")
            
            # Start capture
            capture.start()
            print("   🚀 Capture started")
            
            # Monitor for 10 seconds
            packet_count = 0
            start_time = time.time()
            
            while time.time() - start_time < 10:
                packet = capture.get_packet_nowait()
                if packet:
                    packet_count += 1
                    if packet_count <= 3:  # Show first 3 packets
                        print(f"   📦 Packet {packet_count}: {packet.src_ip}:{packet.src_port} -> {packet.dst_ip}:{packet.dst_port} ({packet.protocol})")
                else:
                    time.sleep(0.1)
            
            capture.stop()
            
            self.results['packet_capture'] = {
                'working': packet_count > 0,
                'packets_captured': packet_count,
                'interface': capture.interface
            }
            
            if packet_count > 0:
                print(f"   ✅ SUCCESS: Captured {packet_count} packets")
                return True
            else:
                print(f"   ❌ FAILED: No packets captured")
                print(f"      - Try running as administrator")
                print(f"      - Check if interface '{capture.interface}' is active")
                print(f"      - Generate network traffic (browse web, ping)")
                return False
                
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            self.results['packet_capture'] = {'working': False, 'error': str(e)}
            return False
    
    def test_feature_extraction(self):
        """Test feature extraction"""
        print("\n2️⃣ Testing Feature Extraction...")
        
        try:
            extractor = FeatureExtractor(window_size=5)
            
            # Create test packet
            test_packet = PacketInfo(
                timestamp=time.time(),
                src_ip="192.168.1.100",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=80,
                protocol="tcp",
                packet_size=1024,
                payload_size=512,
                payload=b"test payload",
                tcp_flags=0x02,  # SYN flag as integer
                tcp_window=8192,
                tcp_seq=1000,
                tcp_ack=0,
                ttl=64,
                ip_flags=0
            )
            
            # Extract features
            features = extractor.extract_features(test_packet)
            
            print(f"   ✅ SUCCESS: Features extracted")
            print(f"      - Flow key: {features.flow_key.src_ip} -> {features.flow_key.dst_ip}")
            print(f"      - Packet size: {features.packet_size}")
            print(f"      - Protocol: {features.flow_key.protocol}")
            
            self.results['feature_extraction'] = {
                'working': True,
                'features_count': len(features.__dict__)
            }
            
            return features
            
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            self.results['feature_extraction'] = {'working': False, 'error': str(e)}
            return None
    
    def test_model_prediction(self, features):
        """Test model prediction"""
        print("\n3️⃣ Testing Model Prediction...")
        
        if not features:
            print("   ⏭️  SKIPPED: No features to test with")
            return None
        
        try:
            model = SimpleModelAdapter()
            
            # Make prediction
            prediction = model.predict(features)
            
            print(f"   ✅ SUCCESS: Prediction made")
            print(f"      - Is attack: {prediction.is_attack}")
            print(f"      - Probability: {prediction.attack_probability:.3f}")
            print(f"      - Threshold: {model.binary_threshold}")
            
            if prediction.is_attack:
                print(f"      - Attack class: {prediction.attack_class}")
            else:
                print(f"      - Classified as normal traffic")
            
            self.results['model_prediction'] = {
                'working': True,
                'is_attack': prediction.is_attack,
                'probability': prediction.attack_probability,
                'threshold': model.binary_threshold
            }
            
            return prediction
            
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            self.results['model_prediction'] = {'working': False, 'error': str(e)}
            return None
    
    def test_alert_generation(self, prediction):
        """Test alert generation"""
        print("\n4️⃣ Testing Alert Generation...")
        
        if not prediction:
            print("   ⏭️  SKIPPED: No prediction to test with")
            return None
        
        try:
            alert_manager = AlertManager(
                toast_enabled=False,  # Disable for testing
                min_confidence=0.1    # Very low threshold
            )
            
            # Generate alert
            alert = alert_manager.generate_alert(prediction)
            
            if alert:
                print(f"   ✅ SUCCESS: Alert generated")
                print(f"      - Alert ID: {alert.alert_id}")
                print(f"      - Attack type: {alert.attack_type}")
                print(f"      - Severity: {alert.severity}")
                print(f"      - Description: {alert.description}")
                
                # Check if alert is stored
                recent_alerts = alert_manager.get_recent_alerts(5)
                print(f"      - Stored alerts: {len(recent_alerts)}")
                
                self.results['alert_generation'] = {
                    'working': True,
                    'alert_generated': True,
                    'stored_alerts': len(recent_alerts)
                }
                
                return alert
            else:
                print(f"   ⚠️  No alert generated")
                print(f"      - Prediction was attack: {prediction.is_attack}")
                print(f"      - Confidence: {prediction.attack_probability:.3f}")
                print(f"      - Min confidence: {alert_manager.min_confidence}")
                
                self.results['alert_generation'] = {
                    'working': True,
                    'alert_generated': False,
                    'reason': 'Below threshold or cooldown'
                }
                
                return None
                
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            self.results['alert_generation'] = {'working': False, 'error': str(e)}
            return None
    
    def test_full_nids_system(self):
        """Test the complete NIDS system"""
        print("\n5️⃣ Testing Full NIDS System...")
        
        config_path = "backend/config.yaml"
        if not Path(config_path).exists():
            print(f"   ❌ FAILED: Config file not found: {config_path}")
            return False
        
        try:
            # Initialize NIDS
            nids = RealTimeNIDS(config_path)
            print(f"   📋 NIDS initialized")
            
            # Check components
            print(f"      - Capture: {type(nids.capture).__name__}")
            print(f"      - Model: {type(nids.model_adapter).__name__}")
            print(f"      - Alerts: {type(nids.alert_manager).__name__}")
            
            # Start detection
            nids.start_detection()
            print(f"   🚀 Detection started")
            
            # Monitor for 15 seconds
            print(f"   ⏱️  Monitoring for 15 seconds...")
            
            initial_stats = nids.get_status()
            time.sleep(15)
            final_stats = nids.get_status()
            
            # Stop detection
            nids.stop_detection()
            
            packets_processed = final_stats['packets_processed'] - initial_stats['packets_processed']
            alerts_generated = final_stats['alerts_generated'] - initial_stats['alerts_generated']
            
            print(f"   📊 Results:")
            print(f"      - Packets processed: {packets_processed}")
            print(f"      - Alerts generated: {alerts_generated}")
            print(f"      - Active flows: {final_stats['active_flows']}")
            
            self.results['full_system'] = {
                'working': True,
                'packets_processed': packets_processed,
                'alerts_generated': alerts_generated,
                'active_flows': final_stats['active_flows']
            }
            
            if packets_processed == 0:
                print(f"   ⚠️  ISSUE: No packets processed by NIDS")
                return False
            elif alerts_generated == 0:
                print(f"   ⚠️  ISSUE: Packets processed but no alerts generated")
                return False
            else:
                print(f"   ✅ SUCCESS: Full system working")
                return True
                
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            self.results['full_system'] = {'working': False, 'error': str(e)}
            return False
    
    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 60)
        print("🔍 PIPELINE DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        for step, result in self.results.items():
            status = "✅ WORKING" if result.get('working', False) else "❌ FAILED"
            print(f"{step.replace('_', ' ').title()}: {status}")
            
            if not result.get('working', False) and 'error' in result:
                print(f"   Error: {result['error']}")
        
        print("\n🎯 ROOT CAUSE ANALYSIS:")
        
        if not self.results.get('packet_capture', {}).get('working', False):
            print("❌ PACKET CAPTURE is the root issue!")
            print("   Solutions:")
            print("   - Run as administrator/root")
            print("   - Check network interface is active")
            print("   - Ensure Npcap/WinPcap is installed")
            print("   - Generate network traffic during test")
        
        elif not self.results.get('model_prediction', {}).get('working', False):
            print("❌ MODEL PREDICTION is the issue!")
            print("   Solutions:")
            print("   - Check model dependencies")
            print("   - Lower detection threshold")
        
        elif not self.results.get('alert_generation', {}).get('working', False):
            print("❌ ALERT GENERATION is the issue!")
            print("   Solutions:")
            print("   - Lower min_confidence threshold")
            print("   - Check alert cooldown settings")
        
        elif self.results.get('full_system', {}).get('packets_processed', 0) == 0:
            print("❌ FULL SYSTEM: No packets being processed!")
            print("   This is likely a packet capture or interface issue")
        
        elif self.results.get('full_system', {}).get('alerts_generated', 0) == 0:
            print("❌ FULL SYSTEM: Packets processed but no alerts!")
            print("   This is likely a model sensitivity issue")
        
        else:
            print("✅ All components working! The issue may be:")
            print("   - Attack patterns not matching detection rules")
            print("   - Network interface not seeing attack traffic")
            print("   - Attack traffic not reaching the monitored interface")

def main():
    """Main diagnostic function"""
    print("🕷️  NIDS Pipeline Diagnostic Tool")
    print("=" * 50)
    print("This will find exactly where the real packet detection is failing")
    print()
    
    diagnostic = PipelineDiagnostic()
    
    # Test each component
    capture_ok = diagnostic.test_packet_capture()
    features = diagnostic.test_feature_extraction()
    prediction = diagnostic.test_model_prediction(features)
    alert = diagnostic.test_alert_generation(prediction)
    
    # Test full system if individual components work
    if capture_ok:
        print("\n💡 Individual components look good, testing full system...")
        diagnostic.test_full_nids_system()
    
    # Print summary
    diagnostic.print_summary()

if __name__ == "__main__":
    main()