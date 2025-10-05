#!/usr/bin/env python3
"""
Fix Network Interface - Find correct interface for localhost traffic
"""

import time
import yaml
from pathlib import Path
from scapy.all import *

def find_active_interfaces():
    """Find all active network interfaces"""
    print("🔌 Finding Active Network Interfaces...")
    
    interfaces = get_if_list()
    active_interfaces = []
    
    print(f"📋 Found {len(interfaces)} total interfaces:")
    
    for i, iface in enumerate(interfaces, 1):
        print(f"   {i}. {iface}")
        
        # Test each interface for traffic
        try:
            print(f"      Testing {iface}...")
            packets = sniff(iface=iface, timeout=2, count=1, store=True)
            
            if packets:
                active_interfaces.append(iface)
                print(f"      ✅ ACTIVE - captured traffic")
            else:
                print(f"      ⚠️  No traffic in 2 seconds")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    return active_interfaces

def test_localhost_interface():
    """Test which interface captures localhost traffic"""
    print("\n🏠 Testing Localhost Traffic Capture...")
    
    interfaces = get_if_list()
    
    # Look for loopback interfaces
    loopback_candidates = []
    for iface in interfaces:
        if any(keyword in iface.lower() for keyword in ['loopback', 'lo', 'local']):
            loopback_candidates.append(iface)
    
    if loopback_candidates:
        print(f"🔍 Found loopback candidates: {loopback_candidates}")
        return loopback_candidates[0]
    
    # Test all interfaces for localhost capture
    print("🧪 Testing all interfaces for localhost capture...")
    
    for iface in interfaces:
        try:
            print(f"   Testing {iface} for localhost...")
            
            # Try to capture on this interface
            packets = sniff(iface=iface, filter="host 127.0.0.1", timeout=1, count=1, store=True)
            
            if packets:
                print(f"   ✅ {iface} can capture localhost traffic!")
                return iface
            
        except Exception as e:
            print(f"   ❌ {iface} failed: {e}")
    
    return None

def update_config_interface(new_interface):
    """Update config.yaml with correct interface"""
    config_path = Path("backend/config.yaml")
    
    try:
        # Load config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update interface
        old_interface = config.get('capture', {}).get('interface', 'unknown')
        config['capture']['interface'] = new_interface
        
        # Save config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"✅ Updated config: {old_interface} → {new_interface}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        return False

def test_interface_with_attack():
    """Test interface by generating test traffic"""
    print("\n🧪 Testing Interface with Real Traffic...")
    
    # Generate some localhost traffic
    try:
        print("📡 Generating test traffic to localhost...")
        
        # Send some test packets to localhost
        for i in range(5):
            packet = IP(dst="127.0.0.1")/TCP(dport=80, flags="S")
            send(packet, verbose=0)
            time.sleep(0.1)
        
        print("✅ Test traffic sent to 127.0.0.1")
        
    except Exception as e:
        print(f"❌ Failed to generate test traffic: {e}")

def main():
    """Main interface fixing function"""
    print("🕷️  Network Interface Fixer")
    print("=" * 40)
    print("Finding the correct interface for ML packet capture...")
    
    # Find active interfaces
    active_interfaces = find_active_interfaces()
    
    if not active_interfaces:
        print("\n❌ No active interfaces found!")
        print("💡 Try running as administrator")
        return
    
    print(f"\n✅ Found {len(active_interfaces)} active interfaces:")
    for iface in active_interfaces:
        print(f"   - {iface}")
    
    # Test for localhost interface
    localhost_interface = test_localhost_interface()
    
    if localhost_interface:
        print(f"\n🎯 Best interface for localhost: {localhost_interface}")
        
        # Update config
        if update_config_interface(localhost_interface):
            print("\n🎉 Interface configuration updated!")
            print("💡 Now restart your ML pipeline:")
            print("   python debug_ml_pipeline.py")
        
    else:
        print("\n⚠️  No interface found for localhost traffic")
        print("💡 Try using the first active interface:")
        
        if active_interfaces:
            best_interface = active_interfaces[0]
            print(f"   Suggested: {best_interface}")
            
            choice = input(f"\nUse {best_interface}? (y/n): ").lower().strip()
            if choice == 'y':
                if update_config_interface(best_interface):
                    print("✅ Interface updated!")
    
    # Test with traffic
    test_interface_with_attack()
    
    print("\n🔧 Interface Fix Complete!")
    print("📋 Next steps:")
    print("1. Restart ML pipeline: python debug_ml_pipeline.py")
    print("2. Run attacks: python comprehensive_attack.py 127.0.0.1")
    print("3. Check if packets are now captured!")

if __name__ == "__main__":
    main()