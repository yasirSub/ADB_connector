import subprocess
import time
import threading
from typing import List, Dict, Optional

class DeviceManager:
    """Manages device detection, connection, and information retrieval"""
    
    def __init__(self, adb_path: str):
        self.adb_path = adb_path
        self.connected_devices: List[str] = []
        self.device_info: Dict[str, Dict] = {}
    
    def scan_devices(self) -> List[str]:
        """Scan for connected devices"""
        try:
            # Kill ADB server first
            subprocess.run([self.adb_path, "kill-server"], capture_output=True)
            time.sleep(1)
            
            # Start ADB server
            subprocess.run([self.adb_path, "start-server"], capture_output=True)
            time.sleep(2)
            
            # Get device list
            result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip first line
                self.connected_devices = []
                
                for line in lines:
                    if line.strip() and '\t' in line:
                        device_id, status = line.strip().split('\t')
                        if device_id and status == 'device':
                            self.connected_devices.append(device_id)
                
                return self.connected_devices
            else:
                return []
                
        except Exception as e:
            print(f"Error scanning devices: {str(e)}")
            return []
    
    def get_device_info(self, device_id: str) -> Dict:
        """Get detailed information about a device"""
        info = {
            'device_id': device_id,
            'connection_type': 'WiFi' if ':' in device_id else 'USB',
            'status': 'Unknown'
        }
        
        try:
            # Get device model
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.product.model"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                info['device_name'] = result.stdout.strip()
            else:
                info['device_name'] = 'Unknown Device'
            
            # Get Android version
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.build.version.release"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                info['android_version'] = result.stdout.strip()
            else:
                info['android_version'] = 'Unknown'
            
            # Get device manufacturer
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.product.manufacturer"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                info['manufacturer'] = result.stdout.strip()
            else:
                info['manufacturer'] = 'Unknown'
            
            # Get device IP address
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "ip", "route"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'src' in line:
                        ip = line.split('src')[1].strip().split()[0]
                        info['device_ip'] = ip
                        break
                else:
                    info['device_ip'] = 'Unknown'
            else:
                info['device_ip'] = 'Unknown'
            
            # Get battery information
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "dumpsys", "battery"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output = result.stdout
                # Extract battery level
                if 'level:' in output:
                    for line in output.split('\n'):
                        if 'level:' in line:
                            level = line.split(':')[1].strip()
                            info['battery_level'] = f"{level}%"
                            break
                else:
                    info['battery_level'] = 'Unknown'
                
                # Extract charging status
                if 'status:' in output:
                    for line in output.split('\n'):
                        if 'status:' in line:
                            status = line.split(':')[1].strip()
                            info['charging_status'] = status
                            break
                else:
                    info['charging_status'] = 'Unknown'
            else:
                info['battery_level'] = 'Unknown'
                info['charging_status'] = 'Unknown'
            
            # Get developer options status
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "settings", "get", "global", "adb_enabled"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                adb_enabled = result.stdout.strip()
                info['developer_options'] = 'Enabled' if adb_enabled == '1' else 'Disabled'
            else:
                info['developer_options'] = 'Unknown'
            
            # Get USB debugging status
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "settings", "get", "global", "adb_wifi_enabled"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                wifi_enabled = result.stdout.strip()
                info['wifi_debugging'] = 'Enabled' if wifi_enabled == '1' else 'Disabled'
            else:
                info['wifi_debugging'] = 'Unknown'
            
            # Get device serial number
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.serialno"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                info['serial_number'] = result.stdout.strip()
            else:
                info['serial_number'] = 'Unknown'
            
            # Get device status
            info['status'] = 'Connected'
            
        except Exception as e:
            info['status'] = f'Error: {str(e)}'
            print(f"Error getting device info: {str(e)}")
        
        self.device_info[device_id] = info
        return info
    
    def connect_usb(self, device_id: str) -> bool:
        """Establish USB connection to device"""
        try:
            # First, check if device is already connected
            if device_id in self.connected_devices:
                return True
            
            # Test if we can communicate with the device
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "echo", "Connected"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Add device to connected list
                if device_id not in self.connected_devices:
                    self.connected_devices.append(device_id)
                
                # Get device info
                device_info = self.get_device_info(device_id)
                self.device_info[device_id] = device_info
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error connecting via USB: {str(e)}")
            return False
    
    def connect_wifi(self, device_id: str, ip: str, port: str) -> bool:
        """Connect to device via WiFi"""
        try:
            print(f"Attempting WiFi connection to {ip}:{port}")
            
            # First check if we can reach the IP
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, int(port)))
            sock.close()
            
            if result != 0:
                print(f"Cannot reach {ip}:{port} - connection refused")
                return False
            
            # Try to connect via ADB
            print(f"Connecting via ADB to {ip}:{port}")
            result = subprocess.run([self.adb_path, "connect", f"{ip}:{port}"], 
                                  capture_output=True, text=True, timeout=15)
            
            print(f"ADB connect result: {result.stdout}")
            if result.stderr:
                print(f"ADB connect error: {result.stderr}")
            
            if result.returncode == 0 and "connected" in result.stdout.lower():
                print(f"Successfully connected to {ip}:{port}")
                return True
            else:
                print(f"Failed to connect to {ip}:{port}")
                return False
                
        except Exception as e:
            print(f"Error connecting via WiFi: {str(e)}")
            return False
    
    def disconnect_device(self, device_id: str) -> bool:
        """Disconnect a specific device"""
        try:
            if ':' in device_id:  # WiFi device
                subprocess.run([self.adb_path, "disconnect", device_id], capture_output=True)
            
            if device_id in self.connected_devices:
                self.connected_devices.remove(device_id)
            
            if device_id in self.device_info:
                del self.device_info[device_id]
            
            return True
        except Exception as e:
            print(f"Error disconnecting device: {str(e)}")
            return False
    
    def disconnect_all(self) -> bool:
        """Disconnect all devices"""
        try:
            for device in self.connected_devices[:]:  # Copy list to avoid modification during iteration
                self.disconnect_device(device)
            return True
        except Exception as e:
            print(f"Error disconnecting all devices: {str(e)}")
            return False
    
    def get_pc_ip(self) -> str:
        """Get PC's IP address"""
        try:
            import socket
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except Exception as e:
            print(f"Error getting PC IP: {str(e)}")
            return "Unknown"
    
    def is_device_available(self, device_id: str) -> bool:
        """Check if a device is still available and connected"""
        try:
            # Check if device is in our connected list
            if device_id in self.connected_devices:
                # Verify device is still responding
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "echo", "test"], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            return False
        except Exception as e:
            print(f"Error checking device availability: {str(e)}")
            return False
