import subprocess
import socket
import ipaddress
import threading
import time
from typing import List, Dict, Optional, Tuple
from .subprocess_utils import run_no_window

class NetworkDetector:
    """Detects network information and finds devices on the same network"""
    
    def __init__(self, adb_path: str):
        self.adb_path = adb_path
        self.pc_ip = None
        self.network_mask = None
        self.network_range = None
    
    def detect_pc_network(self) -> Dict[str, str]:
        """Detect PC's network information"""
        try:
            # Get PC hostname and IP
            hostname = socket.gethostname()
            pc_ip = socket.gethostbyname(hostname)
            
            # Get network interface information
            if socket.has_ipv6:
                # Try to get IPv4 address
                for info in socket.getaddrinfo(hostname, None):
                    if info[0] == socket.AF_INET:  # IPv4
                        pc_ip = info[4][0]
                        break
            
            # Get network mask and range
            network_info = self._get_network_info(pc_ip)
            
            self.pc_ip = pc_ip
            self.network_mask = network_info.get('mask', '255.255.255.0')
            self.network_range = network_info.get('network', f"{pc_ip.rsplit('.', 1)[0]}.0/24")
            
            return {
                'pc_ip': pc_ip,
                'network_mask': self.network_mask,
                'network_range': self.network_range,
                'hostname': hostname
            }
            
        except Exception as e:
            print(f"Error detecting PC network: {str(e)}")
            return {
                'pc_ip': 'Unknown',
                'network_mask': 'Unknown',
                'network_range': 'Unknown',
                'hostname': 'Unknown'
            }
    
    def _get_network_info(self, ip: str) -> Dict[str, str]:
        """Get network mask and range from IP"""
        try:
            # Common network masks
            common_masks = ['255.255.255.0', '255.255.0.0', '255.0.0.0']
            
            for mask in common_masks:
                try:
                    network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                    return {
                        'mask': mask,
                        'network': str(network)
                    }
                except:
                    continue
            
            # Default to /24 network
            return {
                'mask': '255.255.255.0',
                'network': f"{ip.rsplit('.', 1)[0]}.0/24"
            }
            
        except Exception as e:
            print(f"Error getting network info: {str(e)}")
            return {
                'mask': '255.255.255.0',
                'network': f"{ip.rsplit('.', 1)[0]}.0/24"
            }
    
    def scan_network_for_devices(self, timeout: int = 30) -> List[Dict[str, str]]:
        """Scan network for potential Android devices"""
        if not self.network_range:
            return []
        
        devices = []
        network = ipaddress.IPv4Network(self.network_range, strict=False)
        
        def scan_ip(ip: str):
            """Scan a single IP address"""
            try:
                # Try to connect to ADB port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, 5555))
                sock.close()
                
                if result == 0:
                    # Port is open, might be an Android device
                    devices.append({
                        'ip': ip,
                        'port': '5555',
                        'status': 'Port Open'
                    })
                    
            except Exception:
                pass
        
        # Scan network in parallel
        threads = []
        for ip in network.hosts():
            thread = threading.Thread(target=scan_ip, args=(str(ip),))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
            # Limit concurrent threads
            if len(threads) >= 50:
                for t in threads:
                    t.join(timeout=1)
                threads = []
        
        # Wait for remaining threads
        for t in threads:
            t.join(timeout=1)
        
        return devices
    
    def find_device_ip_via_usb(self, device_id: str) -> Optional[str]:
        """Find device IP address when connected via USB"""
        try:
            # Get device IP using ADB
            result = run_no_window([
                self.adb_path, "-s", device_id, "shell", "ip", "route"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'src' in line:
                        # Extract IP address from route output
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'src':
                                if i + 1 < len(parts):
                                    return parts[i + 1]
            
            # Alternative method: get IP from network interface
            result = run_no_window([
                self.adb_path, "-s", device_id, "shell", "ip", "addr", "show", "wlan0"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'inet ' in line:
                        ip = line.split()[1].split('/')[0]
                        return ip
            
            return None
            
        except Exception as e:
            print(f"Error finding device IP via USB: {str(e)}")
            return None
    
    def enable_wifi_debugging(self, device_id: str, port: str = "5555") -> bool:
        """Enable WiFi debugging on device"""
        try:
            # Enable WiFi debugging
            result = run_no_window([
                self.adb_path, "-s", device_id, "tcpip", port
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Wait for device to restart ADB
                time.sleep(3)
                return True
            else:
                print(f"Failed to enable WiFi debugging: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error enabling WiFi debugging: {str(e)}")
            return False
    
    def test_connection(self, ip: str, port: str = "5555") -> bool:
        """Test if device is reachable at given IP:port"""
        try:
            # Try to connect to ADB port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, int(port)))
            sock.close()
            
            return result == 0
            
        except Exception as e:
            print(f"Error testing connection: {str(e)}")
            return False
    
    def get_network_status(self) -> Dict[str, str]:
        """Get current network status"""
        if not self.pc_ip:
            self.detect_pc_network()
        
        return {
            'pc_ip': self.pc_ip or 'Unknown',
            'network_mask': self.network_mask or 'Unknown',
            'network_range': self.network_range or 'Unknown',
            'status': 'Connected' if self.pc_ip else 'Disconnected'
        }
    
    def is_same_network(self, device_ip: str) -> bool:
        """Check if device is on the same network as PC"""
        try:
            if not self.pc_ip or not self.network_mask:
                return False
            
            pc_network = ipaddress.IPv4Network(f"{self.pc_ip}/{self.network_mask}", strict=False)
            device_network = ipaddress.IPv4Network(f"{device_ip}/{self.network_mask}", strict=False)
            
            return pc_network == device_network
            
        except Exception as e:
            print(f"Error checking network: {str(e)}")
            return False
