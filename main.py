#!/usr/bin/env python3
"""
Phone Connector - Debug & Testing Tool
Main application file that integrates all modules
"""

import tkinter as tk
import threading
import sys
import os
import json
import subprocess
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.adb_finder import ADBFinder
from src.device_manager import DeviceManager
from src.connection_manager import ConnectionManager
from src.gui_manager import GUIManager
from src.network_detector import NetworkDetector

class PhoneConnectorApp:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        self.root = tk.Tk()
        
        # Initialize components
        self.adb_path = None
        self.device_manager = None
        self.connection_manager = None
        self.gui_manager = None
        self.network_detector = None
        
        # Initialize application
        self.initialize_app()
    
    def initialize_app(self):
        """Initialize the application components"""
        # Find ADB
        self.adb_path = ADBFinder.find_adb()
        
        if not self.adb_path:
            self.show_adb_error()
            return
        
        # Initialize managers
        self.device_manager = DeviceManager(self.adb_path)
        self.connection_manager = ConnectionManager(self.adb_path)
        self.network_detector = NetworkDetector(self.adb_path)
        self.gui_manager = GUIManager(self.root)
        
        # Set up callbacks
        self.setup_callbacks()
        
        # Start initial device scan
        self.start_initial_scan()
        
        # Auto-detect network when WiFi mode is selected
        self.auto_detect_network()
        
        # Start automatic device monitoring
        self.start_device_monitoring()
        
        # Load saved WiFi configurations
        self.load_wifi_config()
        
        # Check for network changes and guide user
        self.check_network_status()
        
        # Start automatic WiFi connection detection
        self.start_wifi_auto_detection()
    
    def setup_callbacks(self):
        """Set up callback functions between components"""
        # GUI callbacks
        gui_callbacks = {
            'on_scan_devices': self.handle_scan_devices,
            'on_connect_device': self.handle_connect_device,
            'on_disconnect_all': self.handle_disconnect_all,
            'on_connect_wifi': self.handle_connect_wifi,
            'on_connection_type_change': self.handle_connection_type_change,
            'on_detect_network': self.handle_detect_network,
            'on_scan_network': self.handle_scan_network,
            'on_auto_connect_wifi': self.handle_auto_connect_wifi,
            'on_wifi_setup': self.show_wifi_debugging_setup,
            'on_restart_tcpip': self.handle_restart_tcpip
        }
        self.gui_manager.set_callbacks(gui_callbacks)
        
        # Connection manager callbacks
        connection_callbacks = {
            'on_device_connected': self.handle_device_connected,
            'on_device_disconnected': self.handle_device_disconnected,
            'on_device_info_updated': self.handle_device_info_updated
        }
        self.connection_manager.set_callbacks(connection_callbacks)
    
    def start_initial_scan(self):
        """Start initial device scan in background"""
        def initial_scan():
            try:
                devices = self.connection_manager.scan_devices()
                self.root.after(0, self.update_device_list, devices)
                self.root.after(0, self.gui_manager.update_status, f"Ready - {len(devices)} device(s) found")
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"Initial scan error: {str(e)}")
        
        threading.Thread(target=initial_scan, daemon=True).start()
    
    def auto_detect_network(self):
        """Automatically detect network information"""
        def detect_thread():
            try:
                network_info = self.network_detector.detect_pc_network()
                self.root.after(0, self.gui_manager.update_network_info, network_info)
                self.root.after(0, self.gui_manager.log_message, f"Network detected: {network_info.get('pc_ip', 'Unknown')}")
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"Network detection error: {str(e)}")
        
        threading.Thread(target=detect_thread, daemon=True).start()
    
    def start_device_monitoring(self):
        """Start automatic device monitoring in background"""
        def monitor_devices():
            last_devices = set()
            
            while True:
                try:
                    # Get current devices
                    current_devices = set()
                    if self.adb_path:
                        import subprocess
                        result = subprocess.run([self.adb_path, "devices"], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')[1:]  # Skip header
                            for line in lines:
                                if line.strip() and '\t' in line:
                                    device_id = line.split('\t')[0].strip()
                                    status = line.split('\t')[1].strip()
                                    if status == 'device':
                                        current_devices.add(device_id)
                    
                    # Check for new devices
                    new_devices = current_devices - last_devices
                    removed_devices = last_devices - current_devices
                    
                    # Handle new devices
                    for device_id in new_devices:
                        if device_id:
                            self.root.after(0, self.gui_manager.log_message, f"🆕 New device detected: {device_id}")
                            self.root.after(0, self.auto_connect_device, device_id)
                    
                    # Handle removed devices
                    for device_id in removed_devices:
                        if device_id:
                            self.root.after(0, self.gui_manager.log_message, f"❌ Device disconnected: {device_id}")
                            self.root.after(0, self.handle_device_disconnected, device_id)
                    
                    # Update device list if there are changes
                    if new_devices or removed_devices:
                        self.root.after(0, self.update_device_list_from_adb)
                        last_devices = current_devices.copy()
                    
                    # Wait before next check
                    import time
                    time.sleep(2)  # Check every 2 seconds
                    
                except Exception as e:
                    # Log error but continue monitoring
                    self.root.after(0, self.gui_manager.log_message, f"Device monitoring error: {str(e)}")
                    import time
                    time.sleep(5)  # Wait longer on error
        
        # Start monitoring in background thread
        monitoring_thread = threading.Thread(target=monitor_devices, daemon=True)
        monitoring_thread.start()
    
    def auto_connect_device(self, device_id: str):
        """Automatically connect to a newly detected device"""
        try:
            # Check if device is already connected via WiFi
            if device_id in self.connection_manager.connected_devices:
                self.root.after(0, self.gui_manager.log_message, f"✅ Device {device_id} already connected")
                self.root.after(0, self.gui_manager.update_connection_status, f"✅ Connected", "green")
                return
            
            # Create device info
            device_info = {
                'device_id': device_id,
                'status': 'Detected',
                'connection_type': 'USB',
                'device_name': device_id
            }
            
            # Update GUI
            self.root.after(0, self.gui_manager.log_message, f"Auto-connecting to {device_id}...")
            self.root.after(0, self.update_device_info_display, device_info)
            
            # Try to get more device information
            detailed_info = self.get_detailed_device_info(device_info)
            if detailed_info:
                self.root.after(0, self.gui_manager.update_detailed_device_info, detailed_info)
            
            # Now try to get WiFi IP and auto-connect
            self.root.after(0, self.gui_manager.log_message, f"🔍 Getting WiFi IP for {device_id}...")
            phone_ip = self.get_device_wifi_ip(device_id)
            
            if phone_ip:
                # Check if phone is on same network as PC
                pc_ip = self.connection_manager.get_pc_ip()
                
                if self.is_same_network(phone_ip, pc_ip):
                    self.root.after(0, self.gui_manager.log_message, f"🌐 Phone WiFi IP detected: {phone_ip}")
                    self.root.after(0, self.gui_manager.log_message, f"🔄 Attempting automatic WiFi connection...")
                    
                    # Try automatic WiFi connection
                    if self.auto_connect_wifi(phone_ip):
                        self.root.after(0, self.gui_manager.log_message, f"🎉 Auto-connected to {phone_ip} via WiFi!")
                        self.root.after(0, self.gui_manager.update_connection_status, f"✅ Connected to {phone_ip}", "green")
                        self.root.after(0, self.gui_manager.update_auto_connection_status, f"✅ Connected to {phone_ip}", "green")
                        
                        # Auto-fill the IP field with the correct IP
                        self.root.after(0, self.gui_manager.ip_entry.delete, 0, tk.END)
                        self.root.after(0, self.gui_manager.ip_entry.insert, 0, phone_ip)
                        
                        # Mark device as connected to prevent reconnection loop
                        self.connection_manager.connected_devices.add(device_id)
                        return
                    else:
                        self.root.after(0, self.gui_manager.log_message, f"⚠️ Auto WiFi connection failed, keeping USB connection")
                        self.root.after(0, self.gui_manager.update_connection_status, f"📱 USB Connected", "blue")
                else:
                    self.root.after(0, self.gui_manager.log_message, f"⚠️ Phone IP {phone_ip} not on same network as PC {pc_ip}")
                    self.root.after(0, self.gui_manager.update_connection_status, f"📱 USB Connected", "blue")
            else:
                self.root.after(0, self.gui_manager.log_message, f"⚠️ Could not get WiFi IP for {device_id}")
                self.root.after(0, self.gui_manager.update_connection_status, f"📱 USB Connected", "blue")
            
        except Exception as e:
            self.root.after(0, self.gui_manager.log_message, f"Auto-connect error: {str(e)}")
            self.root.after(0, self.gui_manager.update_connection_status, f"📱 USB Connected", "blue")
    
    def update_device_list_from_adb(self):
        """Update device list from ADB devices command"""
        try:
            if not self.adb_path:
                return
            
            import subprocess
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                devices = []
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and '\t' in line:
                        device_id = line.split('\t')[0].strip()
                        status = line.split('\t')[1].strip()
                        if status == 'device':
                            devices.append(device_id)
                
                # Update device list in GUI
                self.root.after(0, self.gui_manager.update_device_list, devices)
                self.root.after(0, self.gui_manager.update_status, f"Ready - {len(devices)} device(s) found")
                
        except Exception as e:
            self.root.after(0, self.gui_manager.log_message, f"Error updating device list: {str(e)}")
    
    def handle_scan_devices(self):
        """Handle scan devices button click"""
        self.gui_manager.set_scan_button_state("disabled")
        self.gui_manager.log_message("Scanning for devices...")
        self.gui_manager.update_status("Scanning...")
        
        def scan_thread():
            try:
                devices = self.connection_manager.scan_devices()
                self.root.after(0, self.update_device_list, devices)
                self.root.after(0, self.gui_manager.update_status, f"Ready - {len(devices)} device(s) found")
                self.root.after(0, self.gui_manager.log_message, f"Found {len(devices)} device(s)")
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"Scan error: {str(e)}")
            finally:
                self.root.after(0, self.gui_manager.set_scan_button_state, "normal")
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def handle_detect_network(self):
        """Handle detect network button click"""
        self.gui_manager.set_network_detection_state("disabled")
        self.gui_manager.log_message("Detecting network information...")
        
        def detect_thread():
            try:
                network_info = self.network_detector.detect_pc_network()
                self.root.after(0, self.gui_manager.update_network_info, network_info)
                self.root.after(0, self.gui_manager.log_message, f"Network detected: PC IP: {network_info.get('pc_ip', 'Unknown')}")
                self.root.after(0, self.gui_manager.log_message, f"Network range: {network_info.get('network_range', 'Unknown')}")
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"Network detection error: {str(e)}")
            finally:
                self.root.after(0, self.gui_manager.set_network_detection_state, "normal")
        
        threading.Thread(target=detect_thread, daemon=True).start()
    
    def handle_scan_network(self):
        """Handle scan network button click"""
        self.gui_manager.set_network_detection_state("disabled")
        self.gui_manager.log_message("Scanning network for devices...")
        
        def scan_thread():
            try:
                # Get scan timeout from advanced settings
                advanced_settings = self.gui_manager.get_advanced_wifi_settings()
                timeout = int(advanced_settings.get('scan_timeout', 30))
                
                devices = self.network_detector.scan_network_for_devices(timeout)
                
                if devices:
                    self.root.after(0, self.gui_manager.log_message, f"Found {len(devices)} potential devices on network")
                    for device in devices:
                        self.root.after(0, self.gui_manager.log_message, f"Device found: {device['ip']}:{device['port']} - {device['status']}")
                        
                        # Auto-fill IP field if empty
                        current_ip = self.gui_manager.ip_entry.get().strip()
                        if not current_ip or current_ip == "192.168.1.100":
                            self.root.after(0, self.gui_manager.ip_entry.delete, 0, tk.END)
                            self.root.after(0, self.gui_manager.ip_entry.insert, 0, device['ip'])
                            break
                else:
                    self.root.after(0, self.gui_manager.log_message, "No devices found on network")
                    
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"Network scan error: {str(e)}")
            finally:
                self.root.after(0, self.gui_manager.set_network_detection_state, "normal")
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def handle_auto_connect_wifi(self):
        """Handle auto connect WiFi button click"""
        self.gui_manager.set_network_detection_state("disabled")
        self.gui_manager.log_message("Attempting auto WiFi connection...")
        
        def auto_connect_thread():
            try:
                # First, check if we have any USB devices
                usb_devices = [d for d in self.device_manager.connected_devices if ':' not in d]
                
                if usb_devices:
                    # Use first USB device to get IP
                    device_id = usb_devices[0]
                    device_ip = self.network_detector.find_device_ip_via_usb(device_id)
                    
                    if device_ip:
                        # Check if device is on same network
                        if self.network_detector.is_same_network(device_ip):
                            self.root.after(0, self.gui_manager.log_message, f"Device IP found: {device_ip}")
                            
                            # Enable WiFi debugging
                            if self.network_detector.enable_wifi_debugging(device_id):
                                self.root.after(0, self.gui_manager.log_message, "WiFi debugging enabled")
                                
                                # Try to connect
                                if self.network_detector.test_connection(device_ip, "5555"):
                                    self.root.after(0, self.gui_manager.log_message, f"Auto-connection successful to {device_ip}:5555")
                                    
                                    # Update IP field
                                    self.root.after(0, self.gui_manager.ip_entry.delete, 0, tk.END)
                                    self.root.after(0, self.gui_manager.ip_entry.insert, 0, device_ip)
                                    
                                    # Show success message
                                    self.root.after(0, self.gui_manager.show_info, "Auto-Connect Success", 
                                                  f"Successfully connected to {device_ip}:5555")
                                else:
                                    self.root.after(0, self.gui_manager.log_message, "Auto-connection failed")
                            else:
                                self.root.after(0, self.gui_manager.log_message, "Failed to enable WiFi debugging")
                        else:
                            self.root.after(0, self.gui_manager.log_message, f"Device {device_ip} is not on the same network")
                    else:
                        self.root.after(0, self.gui_manager.log_message, "Could not find device IP via USB")
                        self.root.after(0, self.gui_manager.show_warning, "Auto-Connect", 
                                      "Could not find device IP. Please connect via USB first or enter IP manually.")
                else:
                    self.root.after(0, self.gui_manager.log_message, "No USB devices found for auto-connection")
                    self.root.after(0, self.gui_manager.show_warning, "Auto-Connect", 
                                  "No USB devices found. Please connect a device via USB first.")
                    
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"Auto-connect error: {str(e)}")
            finally:
                self.root.after(0, self.gui_manager.set_network_detection_state, "normal")
        
        threading.Thread(target=auto_connect_thread, daemon=True).start()
    
    def handle_connect_device(self):
        """Handle connect device button click"""
        device_id = self.gui_manager.get_selected_device()
        if not device_id:
            self.gui_manager.show_warning("Warning", "Please select a device first.")
            return
        
        connection_type = self.gui_manager.get_connection_type()
        
        if connection_type == "usb":
            self.connect_device_usb(device_id)
        else:
            self.connect_device_wifi(device_id)
    
    def connect_device_usb(self, device_id: str):
        """Connect to device via USB"""
        self.gui_manager.log_message(f"Connecting to {device_id} via USB...")
        self.gui_manager.update_status(f"Connecting: {device_id}")
        
        def connect_thread():
            try:
                # First check if device is still available
                if not self.device_manager.is_device_available(device_id):
                    self.root.after(0, self.gui_manager.log_message, f"❌ Device {device_id} is no longer available")
                    self.root.after(0, self.gui_manager.show_error, "Error", f"Device {device_id} is no longer available")
                    self.root.after(0, self.gui_manager.update_status, "Ready")
                    return
                
                # Attempt connection
                success = self.connection_manager.connect_device(device_id, "usb")
                
                if success:
                    # Create device info for display
                    device_info = {
                        'device_id': device_id,
                        'status': 'Connected',
                        'connection_type': 'USB',
                        'device_name': device_id
                    }
                    
                    self.root.after(0, self.gui_manager.log_message, f"✅ Successfully connected to {device_id}")
                    self.root.after(0, self.gui_manager.show_info, "Success", f"Connected to {device_id} via USB")
                    self.root.after(0, self.gui_manager.update_status, f"Connected: {device_id}")
                    self.root.after(0, self.update_device_info_display, device_info)
                    
                    # Update connection status
                    self.root.after(0, self.gui_manager.update_connection_status, f"📱 Connected to {device_id}", "green")
                else:
                    self.root.after(0, self.gui_manager.log_message, f"❌ Failed to connect to {device_id}")
                    self.root.after(0, self.gui_manager.show_error, "Error", f"Failed to connect to {device_id}")
                    self.root.after(0, self.gui_manager.update_status, "Ready")
                    self.root.after(0, self.gui_manager.update_connection_status, f"❌ Connection failed", "red")
                    
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"❌ Error connecting: {str(e)}")
                self.root.after(0, self.gui_manager.show_error, "Error", f"Connection error: {str(e)}")
                self.root.after(0, self.gui_manager.update_status, "Ready")
                self.root.after(0, self.gui_manager.update_connection_status, f"❌ Connection error", "red")
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def connect_device_wifi(self, device_id: str):
        """Connect to device via WiFi"""
        ip, port = self.gui_manager.get_wifi_settings()
        
        if not ip or not port:
            self.gui_manager.show_error("Error", "Please enter IP address and port")
            return
        
        self.gui_manager.log_message(f"Connecting to {device_id} via WiFi ({ip}:{port})...")
        self.gui_manager.update_status(f"Connecting via WiFi: {ip}:{port}")
        
        def connect_thread():
            try:
                success = self.connection_manager.connect_device(device_id, "wifi", ip, port)
                
                if success:
                    # Create device info for display
                    device_info = {
                        'device_id': device_id,
                        'status': 'Connected',
                        'connection_type': 'WiFi',
                        'device_name': device_id,
                        'device_ip': ip
                    }
                    
                    self.root.after(0, self.gui_manager.log_message, f"Successfully connected to {device_id} via WiFi")
                    self.root.after(0, self.gui_manager.show_info, "Success", f"Connected to {device_id} via WiFi")
                    self.root.after(0, self.gui_manager.update_status, f"Connected via WiFi: {ip}:{port}")
                    self.root.after(0, self.update_device_info_display, device_info)
                else:
                    self.root.after(0, self.gui_manager.log_message, f"Failed to connect via WiFi")
                    self.root.after(0, self.gui_manager.show_error, "Error", "Failed to connect via WiFi")
                    self.root.after(0, self.gui_manager.update_status, "Ready")
                    
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"WiFi connection error: {str(e)}")
                self.root.after(0, self.gui_manager.show_error, "Error", f"WiFi connection error: {str(e)}")
                self.root.after(0, self.gui_manager.update_status, "Ready")
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def handle_connect_wifi(self):
        """Handle direct WiFi connection"""
        ip, port = self.gui_manager.get_wifi_settings()
        
        if not ip or not port:
            self.gui_manager.show_error("Error", "Please enter IP address and port")
            return
        
        self.gui_manager.log_message(f"🔗 Attempting WiFi connection to {ip}:{port}...")
        self.gui_manager.update_connection_status(f"🔗 Connecting to {ip}...", "orange")
        
        def connect_thread():
            try:
                # First check if the IP is reachable
                self.root.after(0, self.gui_manager.log_message, f"🔍 Testing connection to {ip}:{port}...")
                
                # Test connection first
                test_result = self.network_detector.test_connection(ip, port)
                self.root.after(0, self.gui_manager.log_message, f"🔍 Connection test result: {test_result}")
                
                if test_result:
                    self.root.after(0, self.gui_manager.log_message, f"✅ Connection test successful to {ip}:{port}")
                    
                    # Try to connect directly
                    self.root.after(0, self.gui_manager.log_message, f"🔗 Attempting ADB WiFi connection...")
                    success = self.device_manager.connect_wifi("", ip, port)
                    
                    self.root.after(0, self.gui_manager.log_message, f"🔗 ADB WiFi connection result: {success}")
                    
                    if success:
                        # Add to device list
                        device_id = f"{ip}:{port}"
                        if device_id not in self.device_manager.connected_devices:
                            self.device_manager.connected_devices.append(device_id)
                        
                        # Save successful connection configuration
                        self.save_wifi_config(ip, port)
                        
                        self.root.after(0, self.update_device_list, self.device_manager.connected_devices)
                        self.root.after(0, self.gui_manager.log_message, f"🎉 Successfully connected to {ip}:{port}")
                        self.root.after(0, self.gui_manager.show_info, "Success", f"Connected to {ip}:{port}")
                        self.root.after(0, self.gui_manager.update_status, f"Connected via WiFi: {ip}:{port}")
                        self.root.after(0, self.gui_manager.update_connection_status, f"✅ Connected to {ip}", "green")
                        
                        # Show connection success guidance
                        self.root.after(0, self.show_connection_guidance, "success", ip)
                    else:
                        self.root.after(0, self.gui_manager.log_message, f"❌ WiFi connection failed: {ip}:{port}")
                        self.root.after(0, self.gui_manager.show_error, "Error", "WiFi connection failed. Check if WiFi debugging is enabled on your phone.")
                        self.root.after(0, self.gui_manager.update_connection_status, f"❌ WiFi failed", "red")
                        self.root.after(0, self.show_connection_guidance, "connection_failed", ip)
                else:
                    self.root.after(0, self.gui_manager.log_message, f"❌ Connection test failed: {ip}:{port}")
                    self.root.after(0, self.gui_manager.show_error, "Error", f"Connection test failed to {ip}:{port}. Check:\n1. IP address is correct\n2. Phone is on same WiFi network\n3. WiFi debugging is enabled")
                    self.root.after(0, self.gui_manager.update_connection_status, f"❌ Test failed", "red")
                    self.root.after(0, self.show_connection_guidance, "connection_failed", ip)
                    
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"❌ WiFi connection error: {str(e)}")
                self.root.after(0, self.gui_manager.show_error, "Error", f"WiFi connection error: {str(e)}")
                self.root.after(0, self.gui_manager.update_connection_status, f"❌ Error", "red")
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def handle_disconnect_all(self):
        """Handle disconnect all button click"""
        if not self.device_manager.connected_devices:
            self.gui_manager.show_info("Info", "No devices to disconnect")
            return
        
        try:
            success = self.connection_manager.disconnect_all()
            
            if success:
                self.update_device_list([])
                self.gui_manager.log_message("All devices disconnected")
                self.gui_manager.update_status("Ready")
                self.gui_manager.show_info("Success", "All devices disconnected")
                self.update_device_info_display(None)
            else:
                self.gui_manager.show_error("Error", "Failed to disconnect devices")
                
        except Exception as e:
            self.gui_manager.log_message(f"Error disconnecting: {str(e)}")
            self.gui_manager.show_error("Error", f"Disconnect error: {str(e)}")
    
    def handle_connection_type_change(self):
        """Handle connection type change"""
        # Auto-detect network when WiFi mode is selected
        if self.gui_manager.get_connection_type() == "wifi":
            self.auto_detect_network()
    
    def handle_device_connected(self, device_id: str, device_info: dict):
        """Handle device connected event"""
        self.gui_manager.log_message(f"Device connected: {device_id}")
        self.update_device_info_display(device_info)
    
    def handle_device_disconnected(self, device_id: str):
        """Handle device disconnected event"""
        if device_id:
            self.gui_manager.log_message(f"Device disconnected: {device_id}")
        else:
            self.gui_manager.log_message("All devices disconnected")
        
        self.update_device_info_display(None)
        self.gui_manager.update_status("Ready")
    
    def handle_device_info_updated(self, device_id: str, device_info: dict):
        """Handle device info update event"""
        self.update_device_info_display(device_info)
    
    def update_device_list(self, devices: list):
        """Update the device list in GUI"""
        self.gui_manager.update_device_list(devices)
    
    def update_device_info_display(self, device_info: dict):
        """Update device information display"""
        pc_ip = self.connection_manager.get_pc_ip()
        self.gui_manager.update_device_info(device_info, pc_ip)
        
        # Also update detailed device info if available
        if device_info:
            # Get additional detailed device information
            detailed_info = self.get_detailed_device_info(device_info)
            self.gui_manager.update_detailed_device_info(detailed_info)
        else:
            # Clear detailed info when no device
            self.gui_manager.update_detailed_device_info(None)
    
    def get_detailed_device_info(self, device_info: dict) -> dict:
        """Get detailed device information using ADB commands"""
        detailed_info = {}
        
        try:
            if not self.adb_path:
                return detailed_info
            
            device_id = device_info.get('device_id', '')
            if not device_id:
                return detailed_info
            
            # Get device properties using ADB
            import subprocess
            
            # Get device model and manufacturer
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.product.model"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    detailed_info['model'] = result.stdout.strip()
            except:
                detailed_info['model'] = 'Unknown'
            
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.product.manufacturer"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    detailed_info['manufacturer'] = result.stdout.strip()
            except:
                detailed_info['manufacturer'] = 'Unknown'
            
            # Get Android version and API level
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.build.version.release"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    detailed_info['android_version'] = result.stdout.strip()
            except:
                detailed_info['android_version'] = 'Unknown'
            
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.build.version.sdk"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    detailed_info['api_level'] = f"API {result.stdout.strip()}"
            except:
                detailed_info['api_level'] = 'Unknown'
            
            # Get build information
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.build.display.id"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    detailed_info['build_number'] = result.stdout.strip()
            except:
                detailed_info['build_number'] = 'Unknown'
            
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.build.version.security_patch"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    detailed_info['security_patch'] = result.stdout.strip()
            except:
                detailed_info['security_patch'] = 'Unknown'
            
            # Get battery information
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "dumpsys", "battery"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    output = result.stdout
                    # Extract battery level
                    for line in output.split('\n'):
                        if 'level:' in line:
                            level = line.split(':')[1].strip()
                            detailed_info['battery_level'] = f"{level}%"
                            break
                    else:
                        detailed_info['battery_level'] = 'Unknown'
                    
                    # Extract charging status
                    for line in output.split('\n'):
                        if 'status:' in line:
                            status = line.split(':')[1].strip()
                            if status == '2':
                                detailed_info['charging_status'] = 'Charging'
                            elif status == '3':
                                detailed_info['charging_status'] = 'Discharging'
                            elif status == '4':
                                detailed_info['charging_status'] = 'Not Charging'
                            elif status == '5':
                                detailed_info['charging_status'] = 'Full'
                            else:
                                detailed_info['charging_status'] = 'Unknown'
                            break
                    else:
                        detailed_info['charging_status'] = 'Unknown'
            except:
                detailed_info['battery_level'] = 'Unknown'
                detailed_info['charging_status'] = 'Unknown'
            
            # Get device name
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "getprop", "ro.product.name"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    detailed_info['device_name'] = result.stdout.strip()
            except:
                detailed_info['device_name'] = 'Unknown'
            
            # Get serial number
            detailed_info['serial_number'] = device_id
            
            # Get connection type
            detailed_info['connection_type'] = device_info.get('connection_type', 'Unknown')
            
            # Get device IP (if available)
            detailed_info['device_ip'] = device_info.get('device_ip', 'Unknown')
            
            # Get PC IP
            detailed_info['pc_ip'] = self.connection_manager.get_pc_ip() or 'Unknown'
            
            # Get status
            detailed_info['status'] = device_info.get('status', 'Connected')
            
            # Get developer options status
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "settings", "get", "global", "development_settings_enabled"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    enabled = result.stdout.strip()
                    detailed_info['developer_options'] = 'Enabled' if enabled == '1' else 'Disabled'
                else:
                    detailed_info['developer_options'] = 'Unknown'
            except:
                detailed_info['developer_options'] = 'Unknown'
            
            # Get WiFi debugging status
            try:
                result = subprocess.run([self.adb_path, "-s", device_id, "shell", "settings", "get", "global", "adb_wifi_enabled"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    enabled = result.stdout.strip()
                    detailed_info['wifi_debugging'] = 'Enabled' if enabled == '1' else 'Disabled'
                else:
                    detailed_info['wifi_debugging'] = 'Unknown'
            except:
                detailed_info['wifi_debugging'] = 'Unknown'
                
        except Exception as e:
            # If there's an error, just return basic info
            detailed_info = {
                'device_name': device_info.get('device_name', 'Unknown'),
                'status': device_info.get('status', 'Unknown'),
                'connection_type': device_info.get('connection_type', 'Unknown'),
                'serial_number': device_info.get('device_id', 'Unknown')
            }
        
        return detailed_info
    
    def show_adb_error(self):
        """Show ADB not found error"""
        error_msg = f"""
ADB (Android Debug Bridge) not found!

{ADBFinder.get_installation_instructions()}

Please install ADB and restart the application.
        """
        
        # Create a simple error dialog
        error_dialog = tk.Toplevel(self.root)
        error_dialog.title("ADB Not Found")
        error_dialog.geometry("600x400")
        error_dialog.resizable(True, True)
        
        # Make dialog modal
        error_dialog.transient(self.root)
        error_dialog.grab_set()
        
        # Error message
        msg_label = tk.Label(error_dialog, text="ADB (Android Debug Bridge) not found!", 
                           font=("Arial", 12, "bold"), fg="red")
        msg_label.pack(pady=20)
        
        # Instructions
        instructions = tk.Text(error_dialog, wrap=tk.WORD, height=15, width=70)
        instructions.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        instructions.insert(tk.END, ADBFinder.get_installation_instructions())
        instructions.config(state=tk.DISABLED)
        
        # Close button
        close_button = tk.Button(error_dialog, text="Close", command=error_dialog.destroy)
        close_button.pack(pady=20)
        
        # Center dialog
        error_dialog.update_idletasks()
        x = (error_dialog.winfo_screenwidth() // 2) - (error_dialog.winfo_width() // 2)
        y = (error_dialog.winfo_screenheight() // 2) - (error_dialog.winfo_height() // 2)
        error_dialog.geometry(f"+{x}+{y}")
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nApplication interrupted by user")
        except Exception as e:
            print(f"Application error: {str(e)}")
        finally:
            # Cleanup
            if self.connection_manager:
                self.connection_manager.stop_monitoring()

    def load_wifi_config(self):
        """Load saved WiFi connection configurations"""
        self.config_file = os.path.join(os.path.dirname(__file__), 'wifi_config.json')
        self.wifi_config = {}
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.wifi_config = json.load(f)
                self.gui_manager.log_message("📱 Loaded previous WiFi configurations")
        except Exception as e:
            self.gui_manager.log_message(f"Error loading WiFi config: {str(e)}")
            self.wifi_config = {}
    
    def save_wifi_config(self, ip: str, port: str = "5555"):
        """Save successful WiFi connection configuration"""
        try:
            self.wifi_config = {
                'last_ip': ip,
                'last_port': port,
                'last_connection_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'connection_count': self.wifi_config.get('connection_count', 0) + 1
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(self.wifi_config, f, indent=2)
            
            self.gui_manager.log_message(f"💾 Saved WiFi configuration: {ip}:{port}")
        except Exception as e:
            self.gui_manager.log_message(f"Error saving WiFi config: {str(e)}")
    
    def check_network_status(self):
        """Check network status and guide user through connection issues"""
        def network_check():
            try:
                # Get current PC network info
                current_network = self.network_detector.detect_pc_network()
                current_pc_ip = current_network.get('pc_ip', '')
                
                if not current_pc_ip:
                    self.root.after(0, self.gui_manager.log_message, "⚠️ Cannot detect PC network")
                    return
                
                # Check if we have a saved configuration
                if self.wifi_config.get('last_ip'):
                    last_ip = self.wifi_config['last_ip']
                    
                    # Check if device is on same network
                    if self.is_same_network(last_ip, current_pc_ip):
                        self.root.after(0, self.gui_manager.log_message, f"✅ Same network detected: {current_pc_ip}")
                        self.root.after(0, self.gui_manager.log_message, f"📱 Try connecting to: {last_ip}:{self.wifi_config.get('last_port', '5555')}")
                        
                        # Auto-fill the IP field
                        self.root.after(0, self.gui_manager.ip_entry.delete, 0, tk.END)
                        self.root.after(0, self.gui_manager.ip_entry.insert, 0, last_ip)
                        
                        # Show connection guidance
                        self.root.after(0, self.show_connection_guidance, "same_network", last_ip)
                    else:
                        self.root.after(0, self.gui_manager.log_message, f"⚠️ Network changed! PC: {current_pc_ip}, Last device: {last_ip}")
                        self.root.after(0, self.gui_manager.log_message, "📱 Please connect your phone to the same WiFi network")
                        self.root.after(0, self.show_connection_guidance, "different_network", last_ip)
                else:
                    self.root.after(0, self.gui_manager.log_message, f"🌐 PC connected to: {current_pc_ip}")
                    self.root.after(0, self.gui_manager.log_message, "📱 No previous WiFi connection found")
                    
            except Exception as e:
                self.root.after(0, self.gui_manager.log_message, f"Network check error: {str(e)}")
        
        threading.Thread(target=network_check, daemon=True).start()
    
    def is_same_network(self, ip1: str, ip2: str) -> bool:
        """Check if two IPs are on the same network"""
        try:
            # Simple network check - first 3 octets should match
            parts1 = ip1.split('.')
            parts2 = ip2.split('.')
            
            if len(parts1) == 4 and len(parts2) == 4:
                return parts1[0] == parts2[0] and parts1[1] == parts2[1] and parts1[2] == parts2[2]
            
            return False
        except:
            return False
    
    def show_connection_guidance(self, guidance_type: str, last_ip: str = None):
        """Show connection guidance based on network status"""
        if guidance_type == "same_network":
            title = "Same Network Detected"
            message = f"""✅ Your phone and PC are on the same network!

Previous connection: {last_ip}:{self.wifi_config.get('last_port', '5555')}

To connect:
1. Make sure your phone has WiFi debugging enabled
2. Click "Connect via WiFi" button
3. Or use "Auto Connect" for automatic connection

If connection fails, try connecting via USB first."""
            
        elif guidance_type == "different_network":
            title = "Network Changed"
            message = f"""⚠️ Network change detected!

Your PC is now on a different network than your last connection.

To fix this:
1. Connect your phone to the SAME WiFi network as your PC
2. Or connect via USB cable for automatic IP detection
3. Then try WiFi connection again

Last known device IP: {last_ip}"""
            
        elif guidance_type == "success":
            title = "Connection Successful!"
            message = f"""🎉 Successfully connected to {last_ip}!

Your WiFi connection has been saved for future use.

Next time you open the software:
1. If on the same network: IP will be auto-filled
2. If network changed: You'll be guided to reconnect
3. If connection fails: USB fallback will be suggested"""
            
        elif guidance_type == "connection_failed":
            title = "Connection Failed"
            message = f"""❌ Failed to connect to {last_ip}

Troubleshooting steps:
1. Check if your phone has WiFi debugging enabled
2. Verify both devices are on the same WiFi network
3. Try connecting via USB cable first
4. Use "Auto Connect" button for automatic setup

The tool will remember this IP for future attempts."""
            
        else:
            title = "Connection Help"
            message = """📱 To connect your phone:

Option 1 - WiFi (Recommended):
1. Enable WiFi debugging on your phone
2. Make sure phone and PC are on same WiFi
3. Enter device IP and click "Connect via WiFi"

Option 2 - USB:
1. Connect phone via USB cable
2. Enable USB debugging
3. Click "Connect Selected" button

Option 3 - Auto Connect:
1. Connect phone via USB first
2. Click "Auto Connect" button
3. Tool will automatically switch to WiFi"""
        
        # Show guidance dialog
        self.gui_manager.show_info(title, message)
    
    def show_wifi_debugging_setup(self):
        """Show WiFi debugging setup guide"""
        title = "WiFi Debugging Setup Guide"
        message = """📱 How to Enable WiFi Debugging on Your Phone:

1. 🔧 Enable Developer Options:
   • Go to Settings → About Phone
   • Tap "Build Number" 7 times
   • You'll see "You are now a developer!"

2. 📶 Enable WiFi Debugging:
   • Go to Settings → Developer Options
   • Turn ON "WiFi Debugging"
   • Turn ON "USB Debugging" (if not already on)

3. 🔐 Allow WiFi Debugging:
   • When prompted, tap "Allow"
   • Note the IP address and port shown

4. 🌐 Connect to Same WiFi:
   • Make sure phone and PC are on SAME WiFi network
   • Check the IP address matches your network range

5. 🔗 Test Connection:
   • Use the IP and port shown on your phone
   • Click "Connect via WiFi" button

💡 TIP: If WiFi debugging fails, try:
   • Connect via USB first
   • Use "Auto Connect" button
   • Check firewall settings on PC

❓ Still having issues? Click "Connection Help" for more assistance."""
        
        self.gui_manager.show_info(title, message)

    def start_wifi_auto_detection(self):
        """Start automatic WiFi connection detection"""
        def auto_detect_wifi():
            while True:
                try:
                    # Check if we have any USB devices connected
                    usb_devices = self.get_usb_devices()
                    
                    if usb_devices:
                        # Use USB device to get phone's WiFi IP
                        for device_id in usb_devices:
                            phone_ip = self.get_device_wifi_ip(device_id)
                            
                            if phone_ip:
                                # Check if phone is on same network as PC
                                pc_ip = self.connection_manager.get_pc_ip()
                                
                                if self.is_same_network(phone_ip, pc_ip):
                                    self.root.after(0, self.gui_manager.log_message, f"🌐 Auto-detected phone on WiFi: {phone_ip}")
                                    self.root.after(0, self.gui_manager.update_connection_status, f"📱 Auto-connecting to {phone_ip}...", "orange")
                                    
                                    # Try automatic WiFi connection
                                    if self.auto_connect_wifi(phone_ip):
                                        self.root.after(0, self.gui_manager.log_message, f"🎉 Auto-connected to {phone_ip} via WiFi!")
                                        self.root.after(0, self.gui_manager.update_connection_status, f"✅ Connected to {phone_ip}", "green")
                                        break
                                    else:
                                        self.root.after(0, self.gui_manager.log_message, f"⚠️ Auto-connection failed to {phone_ip}")
                                        self.root.after(0, self.gui_manager.update_connection_status, f"📱 Ready to connect", "blue")
                    
                    # Wait before next check
                    time.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    self.root.after(0, self.gui_manager.log_message, f"Auto-detection error: {str(e)}")
                    time.sleep(15)  # Wait longer on error
        
        # Start auto-detection in background thread
        auto_detect_thread = threading.Thread(target=auto_detect_wifi, daemon=True)
        auto_detect_thread.start()
    
    def get_usb_devices(self) -> list:
        """Get list of USB-connected devices"""
        try:
            if not self.adb_path:
                return []
            
            result = subprocess.run([self.adb_path, "devices"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                devices = []
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and '\t' in line:
                        device_id = line.split('\t')[0].strip()
                        status = line.split('\t')[1].strip()
                        if status == 'device' and ':' not in device_id:  # USB device (no IP:port)
                            devices.append(device_id)
                
                return devices
            return []
            
        except Exception as e:
            print(f"Error getting USB devices: {str(e)}")
            return []
    
    def get_device_wifi_ip(self, device_id: str) -> str:
        """Get WiFi IP address of a USB-connected device"""
        try:
            if not self.adb_path:
                return None
            
            print(f"Getting WiFi IP for device: {device_id}")
            
            # Method 1: Get device's WiFi IP address using 'ip route'
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "ip", "route"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'src' in line:
                        ip = line.split('src')[1].strip().split()[0]
                        if ip and ip != '0.0.0.0' and ip.startswith('192.168'):
                            print(f"Found IP via 'ip route': {ip}")
                            return ip
            
            # Method 2: Get WiFi interface IP using 'ifconfig wlan0'
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "ifconfig", "wlan0"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout
                if 'inet addr:' in output:
                    ip = output.split('inet addr:')[1].split()[0]
                    if ip and ip.startswith('192.168'):
                        print(f"Found IP via 'ifconfig wlan0': {ip}")
                        return ip
                elif 'inet ' in output:
                    ip = output.split('inet ')[1].split()[0]
                    if ip and ip.startswith('192.168'):
                        print(f"Found IP via 'ifconfig wlan0': {ip}")
                        return ip
            
            # Method 3: Get WiFi interface IP using 'ip addr show wlan0'
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "ip", "addr", "show", "wlan0"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout
                if 'inet ' in output:
                    lines = output.split('\n')
                    for line in lines:
                        if 'inet ' in line and '192.168' in line:
                            ip = line.split('inet ')[1].split('/')[0]
                            if ip and ip.startswith('192.168'):
                                print(f"Found IP via 'ip addr show wlan0': {ip}")
                                return ip
            
            # Method 4: Get all network interfaces
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "ip", "addr"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout
                lines = output.split('\n')
                for line in lines:
                    if 'inet ' in line and '192.168' in line and 'wlan' in line:
                        ip = line.split('inet ')[1].split('/')[0]
                        if ip and ip.startswith('192.168'):
                            print(f"Found IP via 'ip addr': {ip}")
                            return ip
            
            print(f"No WiFi IP found for device: {device_id}")
            return None
            
        except Exception as e:
            print(f"Error getting device WiFi IP: {str(e)}")
            return None
    
    def auto_connect_wifi(self, phone_ip: str) -> bool:
        """Automatically connect to phone via WiFi"""
        try:
            port = "5555"  # Default ADB port
            
            # First test if we can reach the phone
            if not self.network_detector.test_connection(phone_ip, port):
                print(f"Cannot reach {phone_ip}:{port}")
                return False
            
            # Try to connect via ADB
            print(f"Auto-connecting to {phone_ip}:{port}")
            success = self.device_manager.connect_wifi("", phone_ip, port)
            
            if success:
                # Add to device list
                device_id = f"{phone_ip}:{port}"
                if device_id not in self.device_manager.connected_devices:
                    self.device_manager.connected_devices.append(device_id)
                
                # Save successful connection
                self.save_wifi_config(phone_ip, port)
                
                # Update GUI
                self.root.after(0, self.update_device_list, self.device_manager.connected_devices)
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Auto-connect error: {str(e)}")
            return False

    def handle_restart_tcpip(self):
        """Handle TCP/IP restart request from GUI"""
        try:
            # Get selected device
            selected_device = self.gui_manager.get_selected_device_id()
            if not selected_device:
                self.gui_manager.log_message("❌ Please select a device first")
                return
            
            # Check if device is connected via USB
            if not self.device_manager.is_device_available(selected_device):
                self.gui_manager.log_message("❌ Device not available via USB")
                return
            
            self.gui_manager.log_message(f"🔄 Restarting TCP/IP on {selected_device}...")
            
            # First disconnect if connected via WiFi
            subprocess.run([self.adb_path, "disconnect", selected_device], 
                         capture_output=True, text=True, timeout=10)
            
            # Wait a moment
            time.sleep(2)
            
            # Restart TCP/IP on the device
            result = subprocess.run([self.adb_path, "-s", selected_device, "tcpip", "5555"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.gui_manager.log_message(f"✅ TCP/IP restarted on {selected_device}")
                self.gui_manager.log_message(f"📱 Device is now ready for WiFi connection")
                self.gui_manager.log_message(f"🔌 Please disconnect and reconnect USB cable if needed")
            else:
                self.gui_manager.log_message(f"❌ Failed to restart TCP/IP: {result.stderr}")
                
        except Exception as e:
            self.gui_manager.log_message(f"❌ TCP/IP restart error: {str(e)}")

    def restart_tcpip(self, device_id: str):
        """Restart TCP/IP on the device to refresh WiFi debugging"""
        try:
            if not self.adb_path:
                self.gui_manager.log_message("❌ ADB not found")
                return False
            
            self.gui_manager.log_message(f"🔄 Restarting TCP/IP on {device_id}...")
            
            # First disconnect if connected
            subprocess.run([self.adb_path, "disconnect", device_id], 
                         capture_output=True, text=True, timeout=10)
            
            # Wait a moment
            time.sleep(2)
            
            # Restart TCP/IP on the device
            result = subprocess.run([self.adb_path, "-s", device_id, "tcpip", "5555"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.gui_manager.log_message(f"✅ TCP/IP restarted on {device_id}")
                self.gui_manager.log_message(f"📱 Please reconnect your device via USB")
                return True
            else:
                self.gui_manager.log_message(f"❌ Failed to restart TCP/IP: {result.stderr}")
                return False
                
        except Exception as e:
            self.gui_manager.log_message(f"❌ TCP/IP restart error: {str(e)}")
            return False

def main():
    """Main entry point"""
    try:
        app = PhoneConnectorApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
