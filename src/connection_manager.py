import threading
import time
from typing import Dict, Optional, Callable
from .device_manager import DeviceManager
from .subprocess_utils import run_no_window

class ConnectionManager:
    """Manages device connections and information updates"""
    
    def __init__(self, adb_path: str):
        self.adb_path = adb_path
        self.connected_devices = set()  # Track connected devices
        self.device_manager = DeviceManager(adb_path)
        self.current_device: Optional[str] = None
        self.current_device_info: Optional[Dict] = None
        self.pc_ip: str = self.device_manager.get_pc_ip()
        
        # Callbacks
        self.on_device_connected: Callable = None
        self.on_device_disconnected: Callable = None
        self.on_device_info_updated: Callable = None
        
        # Background monitoring
        self.monitoring = False
        self.monitor_thread = None
    
    def set_callbacks(self, callbacks: dict):
        """Set callback functions"""
        self.on_device_connected = callbacks.get('on_device_connected')
        self.on_device_disconnected = callbacks.get('on_device_disconnected')
        self.on_device_info_updated = callbacks.get('on_device_info_updated')
    
    def connect_device(self, device_id: str, connection_type: str, wifi_ip: str = None, wifi_port: str = None) -> bool:
        """Connect to a device"""
        try:
            if connection_type == "usb":
                success = self.device_manager.connect_usb(device_id)
            else:  # WiFi
                if not wifi_ip or not wifi_port:
                    return False
                success = self.device_manager.connect_wifi(device_id, wifi_ip, wifi_port)
            
            if success:
                self.current_device = device_id
                self.current_device_info = self.device_manager.get_device_info(device_id)
                
                # Start monitoring
                self.start_monitoring()
                
                # Notify callback
                if self.on_device_connected:
                    self.on_device_connected(device_id, self.current_device_info)
                
                return True
            else:
                # Log the failure reason
                if connection_type == "usb":
                    print(f"USB connection failed for device: {device_id}")
                else:
                    print(f"WiFi connection failed for device: {device_id} at {wifi_ip}:{wifi_port}")
                return False
                
        except Exception as e:
            print(f"Error connecting device: {str(e)}")
            return False
    
    def disconnect_device(self, device_id: str) -> bool:
        """Disconnect a specific device"""
        try:
            success = self.device_manager.disconnect_device(device_id)
            
            if success and device_id == self.current_device:
                self.current_device = None
                self.current_device_info = None
                self.stop_monitoring()
                
                # Notify callback
                if self.on_device_disconnected:
                    self.on_device_disconnected(device_id)
            
            return success
            
        except Exception as e:
            print(f"Error disconnecting device: {str(e)}")
            return False
    
    def disconnect_all(self) -> bool:
        """Disconnect all devices"""
        try:
            success = self.device_manager.disconnect_all()
            
            if success:
                self.current_device = None
                self.current_device_info = None
                self.stop_monitoring()
                
                # Notify callback
                if self.on_device_disconnected:
                    self.on_device_disconnected(None)
            
            return success
            
        except Exception as e:
            print(f"Error disconnecting all devices: {str(e)}")
            return False
    
    def get_current_device_info(self) -> Optional[Dict]:
        """Get current device information"""
        return self.current_device_info
    
    def get_pc_ip(self) -> str:
        """Get PC IP address"""
        return self.pc_ip
    
    def refresh_device_info(self) -> Optional[Dict]:
        """Refresh current device information"""
        if not self.current_device:
            return None
        
        try:
            self.current_device_info = self.device_manager.get_device_info(self.current_device)
            
            # Notify callback
            if self.on_device_info_updated:
                self.on_device_info_updated(self.current_device, self.current_device_info)
            
            return self.current_device_info
            
        except Exception as e:
            print(f"Error refreshing device info: {str(e)}")
            return None
    
    def start_monitoring(self):
        """Start background monitoring of device"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_device, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
    
    def _monitor_device(self):
        """Background thread to monitor device status"""
        while self.monitoring and self.current_device:
            try:
                # Check if device is still connected
                if self.current_device not in self.device_manager.connected_devices:
                    # Device disconnected
                    self.current_device = None
                    self.current_device_info = None
                    self.monitoring = False
                    
                    if self.on_device_disconnected:
                        self.on_device_disconnected(self.current_device)
                    break
                
                # Update device info every 30 seconds
                time.sleep(30)
                if self.monitoring and self.current_device:
                    self.refresh_device_info()
                    
            except Exception as e:
                print(f"Error in device monitoring: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def scan_devices(self) -> list:
        """Scan for available devices"""
        try:
            devices = self.device_manager.scan_devices()
            return devices
        except Exception as e:
            print(f"Error scanning devices: {str(e)}")
            return []
    
    def get_device_list(self) -> list:
        """Get list of connected devices"""
        return self.device_manager.connected_devices.copy()
    
    def is_device_connected(self, device_id: str) -> bool:
        """Check if a specific device is connected"""
        return device_id in self.device_manager.connected_devices
    
    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get information for a specific device"""
        try:
            return self.device_manager.get_device_info(device_id)
        except Exception as e:
            print(f"Error getting device info: {str(e)}")
            return None
