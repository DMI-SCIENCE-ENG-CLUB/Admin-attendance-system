"""
Device Connection Diagnostic Tool
This script helps diagnose connection issues with biometric devices
"""

import socket
import subprocess
import sys
from devices.identix_k20 import IdentiXK20Adapter

def ping_device(ip_address):
    """Test basic network connectivity using ping"""
    print(f"\n[1] Testing network connectivity to {ip_address}...")
    try:
        # Windows uses -n, Linux/Mac uses -c
        param = '-n' if sys.platform.startswith('win') else '-c'
        command = ['ping', param, '4', ip_address]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Device is reachable on the network")
            return True
        else:
            print(f"❌ FAILED: Device is not responding to ping")
            print(f"   This could mean:")
            print(f"   - Device is powered off")
            print(f"   - Wrong IP address")
            print(f"   - Device is on a different network/subnet")
            print(f"   - Firewall is blocking ICMP packets")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: No response from device")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_port_connectivity(ip_address, port=4370):
    """Test if the specific port is open and accepting connections"""
    print(f"\n[2] Testing port {port} connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        if result == 0:
            print(f"✅ SUCCESS: Port {port} is open and accepting connections")
            return True
        else:
            print(f"❌ FAILED: Port {port} is closed or not responding")
            print(f"   Common causes:")
            print(f"   - Device service not running")
            print(f"   - Wrong port number (default is 4370)")
            print(f"   - Firewall blocking the port")
            return False
    except socket.timeout:
        print(f"❌ TIMEOUT: Port {port} did not respond in time")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_device_connection(ip_address, port=4370, timeout=10):
    """Test actual device connection using the adapter"""
    print(f"\n[3] Testing device connection using IdentiXK20Adapter...")
    try:
        device = IdentiXK20Adapter(ip_address, port=port, timeout=timeout)
        
        print(f"   Attempting to connect...")
        if device.connect():
            print(f"✅ SUCCESS: Connected to device!")
            
            # Try to get device info
            print(f"\n[4] Retrieving device information...")
            try:
                info = device.get_device_info()
                print(f"   Device Name: {info.get('device_name', 'Unknown')}")
                print(f"   Serial Number: {info.get('serial', 'Unknown')}")
                print(f"   Firmware: {info.get('firmware', 'Unknown')}")
                print(f"   Platform: {info.get('platform', 'Unknown')}")
                print(f"   MAC Address: {info.get('mac', 'Unknown')}")
            except Exception as e:
                print(f"   ⚠️  Could not retrieve device info: {str(e)}")
            
            # Try to get user count
            print(f"\n[5] Checking registered users...")
            try:
                users = device.get_users()
                print(f"   ✅ Found {len(users)} registered users")
            except Exception as e:
                print(f"   ⚠️  Could not retrieve users: {str(e)}")
            
            device.disconnect()
            print(f"\n✅ Device disconnected successfully")
            return True
        else:
            print(f"❌ FAILED: Could not establish connection to device")
            print(f"   Possible issues:")
            print(f"   - Device password is incorrect (default: 0)")
            print(f"   - Device firmware incompatibility")
            print(f"   - Device is in use by another application")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"\n   Detailed error information:")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def get_network_info():
    """Display local network information"""
    print(f"\n[0] Local Network Information:")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"   Computer Name: {hostname}")
        print(f"   Local IP Address: {local_ip}")
        
        # Check if device IP is in same subnet
        return local_ip
    except Exception as e:
        print(f"   Could not retrieve network info: {str(e)}")
        return None

def main():
    print("="*60)
    print("   BIOMETRIC DEVICE CONNECTION DIAGNOSTIC TOOL")
    print("="*60)
    
    # Get IP address from user
    default_ip = "192.168.1.1"
    ip_input = input(f"\nEnter device IP address (press Enter for {default_ip}): ").strip()
    ip_address = ip_input if ip_input else default_ip
    
    # Get port from user
    default_port = 4370
    port_input = input(f"Enter device port (press Enter for {default_port}): ").strip()
    port = int(port_input) if port_input else default_port
    
    print(f"\nTesting connection to: {ip_address}:{port}")
    print("="*60)
    
    # Run diagnostics
    local_ip = get_network_info()
    
    # Check if IPs are in same subnet (basic check)
    if local_ip and ip_address:
        local_subnet = '.'.join(local_ip.split('.')[:3])
        device_subnet = '.'.join(ip_address.split('.')[:3])
        if local_subnet != device_subnet:
            print(f"\n⚠️  WARNING: Device appears to be on a different subnet!")
            print(f"   Your subnet: {local_subnet}.x")
            print(f"   Device subnet: {device_subnet}.x")
            print(f"   This may cause connection issues.\n")
    
    ping_ok = ping_device(ip_address)
    port_ok = test_port_connectivity(ip_address, port)
    device_ok = test_device_connection(ip_address, port)
    
    # Summary
    print("\n" + "="*60)
    print("   DIAGNOSTIC SUMMARY")
    print("="*60)
    print(f"   Network Ping: {'✅ PASS' if ping_ok else '❌ FAIL'}")
    print(f"   Port {port} Open: {'✅ PASS' if port_ok else '❌ FAIL'}")
    print(f"   Device Connection: {'✅ PASS' if device_ok else '❌ FAIL'}")
    print("="*60)
    
    if not ping_ok:
        print("\n📋 RECOMMENDATIONS:")
        print("   1. Verify the device IP address is correct")
        print("   2. Check if the device is powered on")
        print("   3. Ensure your computer and device are on the same network")
        print("   4. Check network cables (if using wired connection)")
        print("   5. Try accessing the device's web interface (if available)")
    elif not port_ok:
        print("\n📋 RECOMMENDATIONS:")
        print("   1. Verify the port number (default is 4370)")
        print("   2. Check if a firewall is blocking the port")
        print("   3. Ensure the device service is running")
        print("   4. Try restarting the device")
    elif not device_ok:
        print("\n📋 RECOMMENDATIONS:")
        print("   1. Check if the device password is correct (default: 0)")
        print("   2. Ensure no other application is connected to the device")
        print("   3. Try power cycling the device")
        print("   4. Check device firmware compatibility")
        print("   5. Review device logs if available")
    else:
        print("\n✅ All tests passed! Device is working correctly.")
    
    print("\n")

if __name__ == "__main__":
    main()
