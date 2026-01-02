# Device Connection Troubleshooting Guide

## Quick Diagnostic

Run the diagnostic tool first:
```bash
python diagnose_device.py
```

This will automatically test:
- Network connectivity (ping)
- Port availability
- Device connection
- Device information retrieval

---

## Common Issues and Solutions

### 1. ❌ "Connection failed. Check IP and network."

**Possible Causes:**
- Wrong IP address
- Device is powered off
- Network connectivity issues
- Device on different subnet

**Solutions:**

#### A. Verify IP Address
1. Check the device's display panel for its IP address
2. Access the device's admin menu (usually via keypad)
3. Look for Network Settings → IP Address
4. Common default IPs: `192.168.1.201`, `192.168.1.100`, `192.168.0.100`

#### B. Check Device Power
1. Ensure the device is powered on
2. Check if the screen is active
3. Verify power cable connections

#### C. Test Network Connectivity
```bash
# Windows
ping 192.168.1.198

# If ping fails, the device is not reachable
```

#### D. Verify Same Network
1. Check your computer's IP address:
   - Windows: `ipconfig` in Command Prompt
   - Look for "IPv4 Address"
2. Ensure your computer and device are on the same subnet
   - Example: Computer `192.168.1.100`, Device `192.168.1.198` ✅
   - Example: Computer `192.168.0.100`, Device `192.168.1.198` ❌

---

### 2. ❌ "Connection timeout"

**Possible Causes:**
- Firewall blocking connection
- Wrong port number
- Device service not running

**Solutions:**

#### A. Check Firewall
**Windows Firewall:**
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Ensure Python is allowed on Private networks
4. Or temporarily disable firewall to test

#### B. Verify Port Number
- Default port for ZK devices: **4370**
- Check device documentation for correct port
- Try common alternatives: `4370`, `4380`, `80`

#### C. Test Port Connectivity
```bash
# Windows PowerShell
Test-NetConnection -ComputerName 192.168.1.198 -Port 4370
```

---

### 3. ❌ "Device is in use by another application"

**Possible Causes:**
- Another instance of the app is running
- Device management software is connected
- Previous connection wasn't closed properly

**Solutions:**

1. **Close all instances** of the attendance app
2. **Check Task Manager** for any Python processes
3. **Restart the device**:
   - Power cycle the device
   - Wait 30 seconds
   - Power back on
4. **Check for other software** that might be connected

---

### 4. ❌ "Authentication failed" or "Invalid password"

**Possible Causes:**
- Wrong device password
- Device password was changed

**Solutions:**

1. **Default password** is usually `0` (zero)
2. **Check device settings** for password
3. **Update password in code**:
   ```python
   device = IdentiXK20Adapter(ip, port=4370, password=YOUR_PASSWORD)
   ```

---

### 5. ❌ No users found / No attendance records

**Possible Causes:**
- Device has no registered users
- Users not synced properly
- Device memory cleared

**Solutions:**

1. **Register users on device** first
2. **Use device's enrollment feature** to add fingerprints
3. **Verify users exist** on device display
4. **Try manual sync** from the app

---

## Network Configuration Issues

### Device on Different Subnet

**Problem:** Computer is on `192.168.0.x`, device is on `192.168.1.x`

**Solutions:**

#### Option 1: Change Computer IP (Temporary)
1. Open Network Connections
2. Right-click your network adapter → Properties
3. Select IPv4 → Properties
4. Set manual IP: `192.168.1.100`
5. Subnet mask: `255.255.255.0`
6. Gateway: `192.168.1.1`

#### Option 2: Change Device IP
1. Access device admin menu
2. Navigate to Network Settings
3. Change IP to match your subnet (e.g., `192.168.0.198`)
4. Save and restart device

#### Option 3: Use Router (Recommended)
- Connect both computer and device to the same router/switch
- Let DHCP assign IPs automatically

---

## Device-Specific Settings

### IdentiX K20 Configuration

#### Accessing Device Menu
1. Press **Menu** on device
2. Enter admin password (default: `0` or `123456`)
3. Navigate to **Comm** or **Network**

#### Important Settings
- **IP Address**: Set to match your network
- **Subnet Mask**: Usually `255.255.255.0`
- **Gateway**: Your router's IP
- **Port**: Default `4370`
- **Protocol**: TCP/IP

#### Enable Network Communication
1. Go to **Comm** settings
2. Enable **TCP/IP**
3. Disable **RS232/RS485** if not used
4. Save and restart

---

## Advanced Troubleshooting

### 1. Check Device Logs
```python
# Add logging to see detailed errors
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your connection code
```

### 2. Test with Different Timeout
```python
# Try longer timeout
device = IdentiXK20Adapter(ip, timeout=30)  # 30 seconds
```

### 3. Test UDP vs TCP
```python
# The adapter uses force_udp=False by default
# If TCP fails, try UDP
device = IdentiXK20Adapter(ip, port=4370)
device.zk.force_udp = True  # Force UDP mode
```

### 4. Disable Ping Check
```python
# Some devices don't respond to ping
device = IdentiXK20Adapter(ip, port=4370)
device.zk.ommit_ping = True  # Skip ping check
```

---

## Testing Checklist

Before reporting an issue, verify:

- [ ] Device is powered on and screen is active
- [ ] Device IP address is correct
- [ ] Computer and device are on same network
- [ ] Can ping device successfully
- [ ] Port 4370 is not blocked by firewall
- [ ] No other application is connected to device
- [ ] Device password is correct (default: 0)
- [ ] Users are registered on the device
- [ ] Tried restarting both device and computer

---

## Getting Device Information

### Find Device IP Address

**Method 1: From Device Display**
1. Press Menu
2. Navigate to System → Network
3. Note the IP Address

**Method 2: Network Scan**
```bash
# Windows - scan your network
arp -a

# Look for devices in your subnet
```

**Method 3: Router Admin Panel**
1. Log into your router (usually `192.168.1.1` or `192.168.0.1`)
2. Check connected devices list
3. Look for "ZK" or "Access Control" device

---

## Code Modifications for Better Error Handling

### Update the connection code with better error messages:

```python
def test_connection(self):
    from devices.identix_k20 import IdentiXK20Adapter
    import socket
    
    ip = self.ip_input.text().strip()
    if not ip:
        self.console_output.setText("Please enter an IP address.")
        return
    
    # Step 1: Test basic connectivity
    self.console_output.setText(f"Step 1/3: Testing network connectivity to {ip}...")
    QApplication.processEvents()
    
    try:
        # Try to resolve and ping
        socket.gethostbyname(ip)
        self.console_output.setText(f"Step 2/3: Network OK. Testing port 4370...")
        QApplication.processEvents()
        
        # Test port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 4370))
        sock.close()
        
        if result != 0:
            self.console_output.setText(
                f"❌ Port 4370 is not accessible.\n\n"
                f"Possible issues:\n"
                f"- Firewall blocking the port\n"
                f"- Wrong port number\n"
                f"- Device service not running"
            )
            return
        
        self.console_output.setText(f"Step 3/3: Port OK. Connecting to device...")
        QApplication.processEvents()
        
        # Try device connection
        device = IdentiXK20Adapter(ip, timeout=10)
        if device.connect():
            info = device.get_device_info()
            users = device.get_users()
            device.disconnect()
            
            msg = f"✅ Connected successfully!\n\n"
            msg += f"Device: {info.get('device_name', 'Unknown')}\n"
            msg += f"Serial: {info.get('serial', 'Unknown')}\n"
            msg += f"Firmware: {info.get('firmware', 'Unknown')}\n"
            msg += f"Users Found: {len(users)}"
            
            self.console_output.setText(msg)
        else:
            self.console_output.setText(
                f"❌ Device connection failed.\n\n"
                f"Possible issues:\n"
                f"- Wrong password (default: 0)\n"
                f"- Device in use by another app\n"
                f"- Firmware incompatibility"
            )
    except socket.gaierror:
        self.console_output.setText(f"❌ Invalid IP address: {ip}")
    except socket.timeout:
        self.console_output.setText(
            f"❌ Connection timeout.\n\n"
            f"The device is not responding.\n"
            f"Check if device is powered on and on the same network."
        )
    except Exception as e:
        self.console_output.setText(f"❌ Error: {str(e)}\n\nSee logs for details.")
        import logging
        logging.error(f"Connection error: {e}", exc_info=True)
```

---

## Still Having Issues?

1. **Run the diagnostic tool**: `python diagnose_device.py`
2. **Check device manual** for specific configuration
3. **Verify device firmware** is compatible with the library
4. **Try connecting from device manufacturer's software** to verify device works
5. **Check application logs** in `data/logs/app.log`

---

## Contact Information

If you continue to experience issues:
1. Note the exact error message
2. Run the diagnostic tool and save the output
3. Check the device model and firmware version
4. Document your network configuration
