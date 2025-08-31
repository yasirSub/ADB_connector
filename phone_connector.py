import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import os
import sys
from datetime import datetime

class PhoneConnector:
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Connector - Debug & Testing Tool")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Initialize variables
        self.connected_devices = []
        self.adb_path = self.find_adb()
        self.is_scanning = False
        
        # Create GUI
        self.create_widgets()
        
        # Start device scanning
        self.scan_devices()
    
    def find_adb(self):
        """Find ADB executable path"""
        # Common ADB locations
        possible_paths = [
            "adb",  # If in PATH
            "C:\\Users\\%USERNAME%\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
            "C:\\Android\\Sdk\\platform-tools\\adb.exe",
            "/usr/local/bin/adb",
            "/opt/android-sdk/platform-tools/adb"
        ]
        
        for path in possible_paths:
            try:
                if subprocess.run([path, "version"], capture_output=True, check=True):
                    return path
            except:
                continue
        
        return None
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Phone Connector", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Connection type selection
        connection_frame = ttk.LabelFrame(main_frame, text="Connection Type", padding="10")
        connection_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.connection_var = tk.StringVar(value="usb")
        ttk.Radiobutton(connection_frame, text="USB Connection", variable=self.connection_var, 
                       value="usb", command=self.on_connection_change).grid(row=0, column=0, padx=(0, 20))
        ttk.Radiobutton(connection_frame, text="WiFi Connection", variable=self.connection_var, 
                       value="wifi", command=self.on_connection_change).grid(row=0, column=1)
        
        # Device list
        device_frame = ttk.LabelFrame(main_frame, text="Connected Devices", padding="10")
        device_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        device_frame.columnconfigure(0, weight=1)
        device_frame.rowconfigure(1, weight=1)
        
        # Device list header
        ttk.Label(device_frame, text="Available devices:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Device listbox
        self.device_listbox = tk.Listbox(device_frame, height=8)
        self.device_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Scrollbar for device list
        device_scrollbar = ttk.Scrollbar(device_frame, orient=tk.VERTICAL, command=self.device_listbox.yview)
        device_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.device_listbox.configure(yscrollcommand=device_scrollbar.set)
        
        # Control buttons
        button_frame = ttk.Frame(device_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.scan_button = ttk.Button(button_frame, text="Scan Devices", command=self.scan_devices)
        self.scan_button.grid(row=0, column=0, padx=(0, 10))
        
        self.connect_button = ttk.Button(button_frame, text="Connect Selected", command=self.connect_device)
        self.connect_button.grid(row=0, column=1, padx=(0, 10))
        
        self.disconnect_button = ttk.Button(button_frame, text="Disconnect All", command=self.disconnect_all)
        self.disconnect_button.grid(row=0, column=2)
        
        # Status and log
        status_frame = ttk.LabelFrame(main_frame, text="Status & Log", padding="10")
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(1, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(status_frame, height=8, width=80)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # WiFi connection frame (initially hidden)
        self.wifi_frame = ttk.LabelFrame(main_frame, text="WiFi Connection Settings", padding="10")
        self.wifi_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        self.wifi_frame.grid_remove()  # Hide initially
        
        ttk.Label(self.wifi_frame, text="Device IP Address:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.ip_entry = ttk.Entry(self.wifi_frame, width=15)
        self.ip_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        self.ip_entry.insert(0, "192.168.1.100")
        
        ttk.Label(self.wifi_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.port_entry = ttk.Entry(self.wifi_frame, width=8)
        self.port_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        self.port_entry.insert(0, "5555")
        
        self.wifi_connect_button = ttk.Button(self.wifi_frame, text="Connect via WiFi", command=self.connect_wifi)
        self.wifi_connect_button.grid(row=0, column=4, padx=(20, 0))
        
        # Show/hide WiFi frame based on connection type
        self.on_connection_change()
    
    def on_connection_change(self):
        """Show/hide WiFi settings based on connection type"""
        if self.connection_var.get() == "wifi":
            self.wifi_frame.grid()
        else:
            self.wifi_frame.grid_remove()
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def scan_devices(self):
        """Scan for connected devices"""
        if not self.adb_path:
            messagebox.showerror("Error", "ADB not found. Please install Android SDK Platform Tools.")
            return
        
        self.log_message("Scanning for devices...")
        self.status_var.set("Scanning...")
        self.scan_button.config(state="disabled")
        
        # Run scan in separate thread
        threading.Thread(target=self._scan_devices_thread, daemon=True).start()
    
    def _scan_devices_thread(self):
        """Scan devices in background thread"""
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
                
                # Update GUI in main thread
                self.root.after(0, self._update_device_list)
                self.log_message(f"Found {len(self.connected_devices)} device(s)")
            else:
                self.log_message("Error scanning devices")
                
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
        finally:
            self.root.after(0, self._finish_scan)
    
    def _update_device_list(self):
        """Update the device listbox"""
        self.device_listbox.delete(0, tk.END)
        for device in self.connected_devices:
            self.device_listbox.insert(tk.END, device)
    
    def _finish_scan(self):
        """Finish scanning and update UI"""
        self.scan_button.config(state="normal")
        self.status_var.set(f"Ready - {len(self.connected_devices)} device(s) found")
    
    def connect_device(self):
        """Connect to selected device"""
        selection = self.device_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device first.")
            return
        
        device_id = self.connected_devices[selection[0]]
        connection_type = self.connection_var.get()
        
        if connection_type == "usb":
            self._connect_usb(device_id)
        else:
            self._connect_wifi(device_id)
    
    def _connect_usb(self, device_id):
        """Connect via USB"""
        self.log_message(f"Connecting to {device_id} via USB...")
        self.status_var.set(f"Connected: {device_id}")
        
        # Test connection
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", "echo", "Connected"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_message(f"Successfully connected to {device_id}")
                messagebox.showinfo("Success", f"Connected to {device_id} via USB")
            else:
                self.log_message(f"Failed to connect to {device_id}")
                messagebox.showerror("Error", f"Failed to connect to {device_id}")
        except Exception as e:
            self.log_message(f"Error connecting: {str(e)}")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def _connect_wifi(self, device_id):
        """Connect via WiFi"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip or not port:
            messagebox.showerror("Error", "Please enter IP address and port")
            return
        
        self.log_message(f"Connecting to {device_id} via WiFi ({ip}:{port})...")
        self.status_var.set(f"Connecting via WiFi: {ip}:{port}")
        
        try:
            # Enable WiFi debugging on device
            result = subprocess.run([self.adb_path, "-s", device_id, "tcpip", port], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                time.sleep(2)  # Wait for device to restart ADB
                
                # Connect to device via WiFi
                result = subprocess.run([self.adb_path, "connect", f"{ip}:{port}"], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and "connected" in result.stdout.lower():
                    self.log_message(f"Successfully connected to {device_id} via WiFi")
                    messagebox.showinfo("Success", f"Connected to {device_id} via WiFi")
                    self.status_var.set(f"Connected via WiFi: {ip}:{port}")
                else:
                    self.log_message(f"Failed to connect via WiFi: {result.stdout}")
                    messagebox.showerror("Error", "Failed to connect via WiFi")
            else:
                self.log_message(f"Failed to enable WiFi debugging: {result.stderr}")
                messagebox.showerror("Error", "Failed to enable WiFi debugging")
                
        except Exception as e:
            self.log_message(f"Error connecting via WiFi: {str(e)}")
            messagebox.showerror("Error", f"WiFi connection error: {str(e)}")
    
    def connect_wifi(self):
        """Connect to device via WiFi using manual IP/port"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip or not port:
            messagebox.showerror("Error", "Please enter IP address and port")
            return
        
        self.log_message(f"Connecting to {ip}:{port} via WiFi...")
        
        try:
            result = subprocess.run([self.adb_path, "connect", f"{ip}:{port}"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "connected" in result.stdout.lower():
                self.log_message(f"Successfully connected to {ip}:{port}")
                messagebox.showinfo("Success", f"Connected to {ip}:{port}")
                self.status_var.set(f"Connected via WiFi: {ip}:{port}")
                
                # Add to device list
                device_id = f"{ip}:{port}"
                if device_id not in self.connected_devices:
                    self.connected_devices.append(device_id)
                    self._update_device_list()
            else:
                self.log_message(f"Failed to connect: {result.stdout}")
                messagebox.showerror("Error", "Failed to connect via WiFi")
                
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def disconnect_all(self):
        """Disconnect all devices"""
        if not self.connected_devices:
            messagebox.showinfo("Info", "No devices to disconnect")
            return
        
        try:
            for device in self.connected_devices:
                if ':' in device:  # WiFi device
                    subprocess.run([self.adb_path, "disconnect", device], capture_output=True)
                # USB devices will disconnect when cable is removed
            
            self.connected_devices.clear()
            self._update_device_list()
            self.log_message("All devices disconnected")
            self.status_var.set("Ready")
            messagebox.showinfo("Success", "All devices disconnected")
            
        except Exception as e:
            self.log_message(f"Error disconnecting: {str(e)}")
            messagebox.showerror("Error", f"Disconnect error: {str(e)}")

def main():
    root = tk.Tk()
    app = PhoneConnector(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
