"""
Quick Device Connection Test
Automatically tests connection to device at 192.168.1.1
"""

import socket
import subprocess
import sys
from devices.identix_k20 import IdentiXK20Adapter

# Configuration
DEVICE_IP = "192.168.1.1"
DEVICE_PORT = 4370
TIMEOUT = 10

print("="*70)
print("   DEVICE CONNECTION TEST - IP: {}:{}".format(DEVICE_IP, DEVICE_PORT))
print("="*70)

# Step 1: Network connectivity
print("\n[1/4] Testing network connectivity...")
try:
    param = '-n' if sys.platform.startswith('win') else '-c'
    result = subprocess.run(['ping', param, '2', DEVICE_IP], 
                          capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print("      ✅ Device is reachable on network")
        ping_ok = True
    else:
        print("      ❌ Device not responding to ping")
        print("         - Check if device is powered on")
        print("         - Verify IP address is correct")
        ping_ok = False
except Exception as e:
    print(f"      ❌ Ping failed: {str(e)}")
    ping_ok = False

# Step 2: Port connectivity
print("\n[2/4] Testing port {} connectivity...".format(DEVICE_PORT))
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((DEVICE_IP, DEVICE_PORT))
    sock.close()
    
    if result == 0:
        print("      ✅ Port {} is open".format(DEVICE_PORT))
        port_ok = True
    else:
        print("      ❌ Port {} is closed".format(DEVICE_PORT))
        print("         - Check firewall settings")
        print("         - Verify device service is running")
        port_ok = False
except Exception as e:
    print(f"      ❌ Port test failed: {str(e)}")
    port_ok = False

# Step 3: Device connection
print("\n[3/4] Testing device connection...")
try:
    device = IdentiXK20Adapter(DEVICE_IP, port=DEVICE_PORT, timeout=TIMEOUT)
    
    if device.connect():
        print("      ✅ Successfully connected to device!")
        device_ok = True
        
        # Step 4: Get device info
        print("\n[4/4] Retrieving device information...")
        try:
            info = device.get_device_info()
            users = device.get_users()
            
            print("\n" + "="*70)
            print("   DEVICE INFORMATION")
            print("="*70)
            print(f"   Device Name:    {info.get('device_name', 'Unknown')}")
            print(f"   Serial Number:  {info.get('serial', 'Unknown')}")
            print(f"   Firmware:       {info.get('firmware', 'Unknown')}")
            print(f"   Platform:       {info.get('platform', 'Unknown')}")
            print(f"   MAC Address:    {info.get('mac', 'Unknown')}")
            print(f"   Registered Users: {len(users)}")
            print("="*70)
            
        except Exception as e:
            print(f"      ⚠️  Could not retrieve device info: {str(e)}")
        
        device.disconnect()
        print("\n      Device disconnected successfully")
        
    else:
        print("      ❌ Failed to connect to device")
        print("         - Check device password (default: 0)")
        print("         - Ensure device is not in use by another app")
        device_ok = False
        
except Exception as e:
    print(f"      ❌ Connection error: {str(e)}")
    device_ok = False

# Summary
print("\n" + "="*70)
print("   TEST SUMMARY")
print("="*70)
print(f"   Network Ping:       {'✅ PASS' if ping_ok else '❌ FAIL'}")
print(f"   Port {DEVICE_PORT} Open:     {'✅ PASS' if port_ok else '❌ FAIL'}")
print(f"   Device Connection:  {'✅ PASS' if device_ok else '❌ FAIL'}")
print("="*70)

if not ping_ok:
    print("\n⚠️  ISSUE: Device not reachable on network")
    print("\nSOLUTIONS:")
    print("  1. Verify device IP address (check device display)")
    print("  2. Ensure device is powered on")
    print("  3. Check network cables/WiFi connection")
    print("  4. Verify computer and device are on same network")
    
elif not port_ok:
    print("\n⚠️  ISSUE: Port {} not accessible".format(DEVICE_PORT))
    print("\nSOLUTIONS:")
    print("  1. Check Windows Firewall settings")
    print("  2. Verify device service is running")
    print("  3. Try restarting the device")
    print("  4. Confirm port number is correct (default: 4370)")
    
elif not device_ok:
    print("\n⚠️  ISSUE: Cannot establish device connection")
    print("\nSOLUTIONS:")
    print("  1. Check device password (default: 0)")
    print("  2. Close any other apps connected to device")
    print("  3. Power cycle the device")
    print("  4. Check firmware compatibility")
    
else:
    print("\n✅ SUCCESS! Device is working correctly.")
    print("   You can now use the device in your application.")

print("\n")
