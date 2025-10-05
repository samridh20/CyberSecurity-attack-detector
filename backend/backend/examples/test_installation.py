#!/usr/bin/env python3
"""
Installation verification script for the NIDS system.
Tests core functionality without requiring admin privileges.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import numpy
        print("✓ numpy")
    except ImportError as e:
        print(f"✗ numpy: {e}")
        return False
    
    try:
        import pandas
        print("✓ pandas")
    except ImportError as e:
        print(f"✗ pandas: {e}")
        return False
    
    try:
        import sklearn
        print("✓ scikit-learn")
    except ImportError as e:
        print(f"✗ scikit-learn: {e}")
        return False
    
    try:
        import scapy
        print("✓ scapy")
    except ImportError as e:
        print(f"✗ scapy: {e}")
        return False
    
    try:
        import yaml
        print("✓ pyyaml")
    except ImportError as e:
        print(f"✗ pyyaml: {e}")
        return False
    
    try:
        from pydantic import BaseModel
        print("✓ pydantic")
    except ImportError as e:
        print(f"✗ pydantic: {e}")
        return False
    
    # Optional imports
    try:
        import numba
        print("✓ numba (optional)")
    except ImportError:
        print("- numba (optional, not installed)")
    
    try:
        import matplotlib
        print("✓ matplotlib (optional)")
    except ImportError:
        print("- matplotlib (optional, not installed)")
    
    return True

def test_nids_modules():
    """Test NIDS module imports."""
    print("\\nTesting NIDS modules...")
    
    try:
        from nids.schemas import PacketInfo, FeatureVector, ModelPrediction
        print("✓ nids.schemas")
    except Exception as e:
        print(f"✗ nids.schemas: {e}")
        return False
    
    try:
        from nids.features import FeatureExtractor
        print("✓ nids.features")
    except Exception as e:
        print(f"✗ nids.features: {e}")
        return False
    
    try:
        from nids.models import SimpleModelAdapter
        print("✓ nids.models")
    except Exception as e:
        print(f"✗ nids.models: {e}")
        return False
    
    try:
        from nids.alerts import AlertManager
        print("✓ nids.alerts")
    except Exception as e:
        print(f"✗ nids.alerts: {e}")
        return False
    
    try:
        from nids.core import RealTimeNIDS
        print("✓ nids.core")
    except Exception as e:
        print(f"✗ nids.core: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration file loading."""
    print("\\nTesting configuration...")
    
    config_file = Path("config.yaml")
    if not config_file.exists():
        print("✗ config.yaml not found")
        return False
    
    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        print("✓ config.yaml loads successfully")
        
        # Check required sections
        required_sections = ['models', 'capture', 'features', 'alerts']
        for section in required_sections:
            if section in config:
                print(f"✓ config section: {section}")
            else:
                print(f"✗ missing config section: {section}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ config.yaml error: {e}")
        return False

def test_metadata_files():
    """Test metadata file availability."""
    print("\\nTesting metadata files...")
    
    models_dir = Path("models")
    if not models_dir.exists():
        print("✗ models directory not found")
        return False
    
    metadata_files = [
        "feature_order.json",
        "scaler_params.json", 
        "class_encoder.json"
    ]
    
    all_found = True
    for filename in metadata_files:
        filepath = models_dir / filename
        if filepath.exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} not found")
            all_found = False
    
    return all_found

def test_basic_functionality():
    """Test basic NIDS functionality."""
    print("\\nTesting basic functionality...")
    
    try:
        # Test feature extraction
        from nids.features import FeatureExtractor
        from nids.schemas import PacketInfo
        import time
        
        extractor = FeatureExtractor(use_numba=False)
        
        packet = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=80,
            protocol="tcp",
            packet_size=1000,
            payload_size=500,
            payload=b"test data",
            tcp_flags=0x18,
            ttl=64
        )
        
        features = extractor.extract_features(packet)
        print("✓ Feature extraction works")
        
        # Test model prediction
        from nids.models import SimpleModelAdapter
        
        model = SimpleModelAdapter()
        prediction = model.predict(features)
        print("✓ Model prediction works")
        
        # Test alert generation
        from nids.alerts import AlertManager
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            alert_manager = AlertManager(
                toast_enabled=False,
                log_file=f"{temp_dir}/test_alerts.jsonl"
            )
            
            if prediction.is_attack:
                alert = alert_manager.generate_alert(prediction)
                if alert:
                    print("✓ Alert generation works")
                else:
                    print("- Alert generation (no alert generated)")
            else:
                print("- Alert generation (no attack detected)")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_network_interfaces():
    """Test network interface detection."""
    print("\\nTesting network interfaces...")
    
    try:
        from scapy.all import get_if_list
        interfaces = get_if_list()
        
        if interfaces:
            print(f"✓ Found {len(interfaces)} network interfaces:")
            for i, iface in enumerate(interfaces[:5]):  # Show first 5
                print(f"  {i+1}. {iface}")
            if len(interfaces) > 5:
                print(f"  ... and {len(interfaces) - 5} more")
        else:
            print("✗ No network interfaces found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Network interface test failed: {e}")
        return False

def main():
    """Run all installation tests."""
    print("NIDS Installation Verification")
    print("=" * 40)
    
    tests = [
        ("Core Dependencies", test_imports),
        ("NIDS Modules", test_nids_modules),
        ("Configuration", test_configuration),
        ("Metadata Files", test_metadata_files),
        ("Basic Functionality", test_basic_functionality),
        ("Network Interfaces", test_network_interfaces),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\\n{test_name}")
        print("-" * len(test_name))
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\\n" + "=" * 40)
    print("INSTALLATION VERIFICATION SUMMARY")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\\n🎉 Installation verification successful!")
        print("You can now run the NIDS system.")
        print("\\nNext steps:")
        print("- Run demo: python main.py --demo")
        print("- Start real-time detection: python main.py")
        print("- Process PCAP file: python main.py --pcap file.pcap --offline")
        return 0
    else:
        print(f"\\n⚠️  {total - passed} test(s) failed.")
        print("Please check the installation and resolve any issues.")
        print("See INSTALL.md for detailed installation instructions.")
        return 1

if __name__ == "__main__":
    exit(main())