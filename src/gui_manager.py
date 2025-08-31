import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time

class GUIManager:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB Connector - Smart Device Bridge")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Callback functions
        self.on_connect_usb = None
        self.on_connect_wifi = None
        self.on_disconnect = None
        self.on_restart_tcpip = None
        
        # Create the main interface
        self._create_main_interface()
        
        # Bind device selection event
        self.device_listbox.bind('<<ListboxSelect>>', self._on_device_selection)

    def _create_main_interface(self):
        """Create the main interface"""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔌 ADB Connector - Smart Device Bridge", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Device List Frame
        device_frame = ttk.LabelFrame(main_frame, text="📱 Connected Devices", padding="10")
        device_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 10))
        device_frame.columnconfigure(1, weight=1)
        
        # Device listbox with scrollbar
        listbox_frame = ttk.Frame(device_frame)
        listbox_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        listbox_frame.columnconfigure(0, weight=1)
        
        self.device_listbox = tk.Listbox(listbox_frame, height=4, selectmode=tk.SINGLE)
        self.device_listbox.grid(row=0, column=0, sticky="ew")
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.device_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.device_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Device action buttons
        button_frame = ttk.Frame(device_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        self.connect_usb_btn = ttk.Button(button_frame, text="🔌 Connect USB", 
                                         command=self._on_connect_usb_clicked)
        self.connect_usb_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.disconnect_btn = ttk.Button(button_frame, text="❌ Disconnect", 
                                        command=self._on_disconnect_clicked)
        self.disconnect_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Expandable device info section
        self.expand_button = ttk.Button(button_frame, text=">> Show Details", 
                                       command=self._toggle_device_details)
        self.expand_button.grid(row=0, column=2)
        
        # Device info display (basic)
        self.device_info_frame = ttk.LabelFrame(device_frame, text="Device Information", padding="10")
        self.device_info_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # Basic device info labels
        self.device_info_labels = {}
        self._create_device_info_labels()
        
        # Detailed device info frame (initially hidden)
        self.detailed_info_frame = ttk.Frame(self.device_info_frame)
        self.detailed_info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        self.detailed_info_frame.grid_remove()  # Hide initially
        
        # Detailed device info labels
        self.detailed_info_labels = {}
        self._create_detailed_device_info_labels()
        
        # WiFi Connection Frame (Compact)
        wifi_frame = ttk.LabelFrame(main_frame, text="🌐 WiFi Connection", padding="10")
        wifi_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 10))
        wifi_frame.columnconfigure(1, weight=1)
        
        # IP and Port inputs
        ttk.Label(wifi_frame, text="IP:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.ip_entry = ttk.Entry(wifi_frame, width=15)
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.ip_entry.insert(0, "192.168.1.100")
        
        ttk.Label(wifi_frame, text="Port:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.port_entry = ttk.Entry(wifi_frame, width=8)
        self.port_entry.grid(row=0, column=3, sticky="w", padx=(0, 10))
        self.port_entry.insert(0, "5555")
        
        # WiFi action buttons
        self.wifi_connect_button = ttk.Button(wifi_frame, text="🔗 Connect WiFi", 
                                             command=self._on_connect_wifi_clicked)
        self.wifi_connect_button.grid(row=0, column=4, padx=(0, 10))
        
        self.restart_tcpip_button = ttk.Button(wifi_frame, text="🔄 Restart TCP/IP", 
                                              command=self._on_restart_tcpip_clicked)
        self.restart_tcpip_button.grid(row=0, column=5)
        
        # WiFi setup help button
        self.wifi_setup_button = ttk.Button(wifi_frame, text="📱 WiFi Setup Guide", 
                                           command=self._show_wifi_setup)
        self.wifi_setup_button.grid(row=1, column=0, columnspan=6, pady=(10, 0), sticky="ew")
        
        # Status Frame (Compact)
        status_frame = ttk.LabelFrame(main_frame, text="📊 Status", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        # Status indicators
        status_row = ttk.Frame(status_frame)
        status_row.grid(row=0, column=0, sticky="ew")
        status_row.columnconfigure(1, weight=1)
        
        ttk.Label(status_row, text="Monitoring:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.monitoring_status = tk.StringVar(value="🔍 Searching for devices...")
        monitoring_label = ttk.Label(status_row, textvariable=self.monitoring_status, foreground="blue")
        monitoring_label.grid(row=0, column=1, sticky="w")
        
        ttk.Label(status_row, text="Connection:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
        self.connection_status = tk.StringVar(value="📱 Ready to connect")
        connection_label = ttk.Label(status_row, textvariable=self.connection_status, foreground="blue")
        connection_label.grid(row=1, column=1, sticky="w", pady=(5, 0))
        
        # Log Frame
        log_frame = ttk.LabelFrame(main_frame, text="📝 Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text widget with scrollbar
        log_widget_frame = ttk.Frame(log_frame)
        log_widget_frame.grid(row=0, column=0, sticky="nsew")
        log_widget_frame.columnconfigure(0, weight=1)
        log_widget_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_widget_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        log_scrollbar = ttk.Scrollbar(log_widget_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Clear log button
        clear_log_btn = ttk.Button(log_frame, text="🗑️ Clear Log", command=self._clear_log)
        clear_log_btn.grid(row=1, column=0, pady=(10, 0), sticky="w")

    def _create_device_info_labels(self):
        """Create basic device info labels"""
        info_frame = ttk.Frame(self.device_info_frame)
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        info_frame.columnconfigure(1, weight=1)
        
        # Basic info labels
        labels = ['device_id', 'status', 'connection_type', 'pc_ip']
        for i, label in enumerate(labels):
            ttk.Label(info_frame, text=f"{label.replace('_', ' ').title()}:").grid(row=i, column=0, sticky="w", padx=(0, 10))
            label_widget = ttk.Label(info_frame, text="Not connected", foreground="gray")
            label_widget.grid(row=i, column=1, sticky="w")
            self.device_info_labels[label] = label_widget

    def _create_detailed_device_info_labels(self):
        """Create detailed device info labels"""
        # Detailed info labels
        detailed_labels = [
            'device_name', 'android_version', 'build_number', 'manufacturer', 
            'model', 'serial_number', 'battery_level', 'battery_status'
        ]
        
        for i, label in enumerate(detailed_labels):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(self.detailed_info_frame, text=f"{label.replace('_', ' ').title()}:").grid(
                row=row, column=col, sticky="w", padx=(0, 10))
            label_widget = ttk.Label(self.detailed_info_frame, text="N/A", foreground="gray")
            label_widget.grid(row=row, column=col+1, sticky="w", padx=(0, 20))
            self.detailed_info_labels[label] = label_widget

    def _toggle_device_details(self):
        """Toggle the display of detailed device information"""
        if self.detailed_info_frame.winfo_viewable():
            self.detailed_info_frame.grid_remove()
            self.expand_button.configure(text=">> Show Details")
        else:
            self.detailed_info_frame.grid()
            self.expand_button.configure(text="<< Hide Details")

    def _show_wifi_setup(self):
        """Show WiFi debugging setup guide"""
        setup_window = tk.Toplevel(self.root)
        setup_window.title("WiFi Debugging Setup Guide")
        setup_window.geometry("600x500")
        setup_window.resizable(False, False)
        
        # Make window modal
        setup_window.transient(self.root)
        setup_window.grab_set()
        
        # Content
        content_frame = ttk.Frame(setup_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(content_frame, text="📱 WiFi Debugging Setup Guide", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 20))
        
        steps = [
            "1. 🔌 Connect your phone to PC via USB cable",
            "2. 📱 Enable Developer Options on your phone:",
            "   • Go to Settings > About Phone",
            "   • Tap 'Build Number' 7 times",
            "3. 🔧 Enable USB Debugging:",
            "   • Go to Settings > Developer Options",
            "   • Turn ON 'USB Debugging'",
            "4. 🌐 Enable WiFi Debugging:",
            "   • In Developer Options, turn ON 'WiFi Debugging'",
            "   • Note the IP address and port shown",
            "5. 🔌 Disconnect USB cable",
            "6. 📡 Your phone is now ready for WiFi connection!"
        ]
        
        for step in steps:
            label = ttk.Label(content_frame, text=step, justify=tk.LEFT)
            label.pack(anchor=tk.W, pady=2)
        
        # Close button
        close_btn = ttk.Button(content_frame, text="Got it!", command=setup_window.destroy)
        close_btn.pack(pady=(20, 0))

    def _clear_log(self):
        """Clear the log text"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_device_selection(self, event):
        """Handle device selection in listbox"""
        # This method is kept for compatibility but not actively used
        pass

    def _on_connect_usb_clicked(self):
        """Handle USB connect button click"""
        if self.on_connect_usb:
            self.on_connect_usb()

    def _on_connect_wifi_clicked(self):
        """Handle WiFi connect button click"""
        if self.on_connect_wifi:
            self.on_connect_wifi()

    def _on_disconnect_clicked(self):
        """Handle disconnect button click"""
        if self.on_disconnect:
            self.on_disconnect()

    def _on_restart_tcpip_clicked(self):
        """Handle TCP/IP restart button click"""
        if self.on_restart_tcpip:
            self.on_restart_tcpip()

    def set_callbacks(self, callbacks: dict):
        """Set callback functions"""
        self.on_connect_usb = callbacks.get('on_connect_usb')
        self.on_connect_wifi = callbacks.get('on_connect_wifi')
        self.on_disconnect = callbacks.get('on_disconnect')
        self.on_restart_tcpip = callbacks.get('on_restart_tcpip')

    def update_device_info(self, device_info: dict):
        """Update device information display"""
        try:
            for key, label in self.device_info_labels.items():
                if key in device_info:
                    value = device_info[key] or "N/A"
                    label.configure(text=str(value), foreground="black")
                else:
                    label.configure(text="N/A", foreground="gray")
        except Exception as e:
            print(f"Error updating device info: {e}")

    def update_detailed_device_info(self, detailed_info: dict):
        """Update detailed device information display"""
        try:
            for key, label in self.detailed_info_labels.items():
                if key in detailed_info:
                    value = detailed_info[key] or "N/A"
                    label.configure(text=str(value), foreground="black")
                else:
                    label.configure(text="N/A", foreground="gray")
        except Exception as e:
            print(f"Error updating detailed device info: {e}")

    def update_device_list(self, devices: list):
        """Update the device listbox"""
        try:
            self.device_listbox.delete(0, tk.END)
            for device in devices:
                self.device_listbox.insert(tk.END, device)
        except Exception as e:
            print(f"Error updating device list: {e}")

    def get_selected_device_id(self) -> str:
        """Get the currently selected device ID"""
        try:
            selection = self.device_listbox.curselection()
            if selection:
                return self.device_listbox.get(selection[0])
            return ""
        except Exception as e:
            print(f"Error getting selected device: {e}")
            return ""

    def log_message(self, message: str):
        """Add a message to the log"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
            
            # Also print to console for debugging
            print(log_entry.strip())
        except Exception as e:
            print(f"Error logging message: {e}")

    def update_monitoring_status(self, message: str, color: str = "black"):
        """Update monitoring status"""
        try:
            self.monitoring_status.set(message)
            # Find the label and update its color
            for child in self.root.winfo_children():
                for grandchild in child.winfo_children():
                    if hasattr(grandchild, 'cget'):
                        try:
                            if grandchild.cget('textvariable') == str(self.monitoring_status):
                                grandchild.configure(foreground=color)
                                break
                        except:
                            continue
        except Exception as e:
            print(f"Error updating monitoring status: {e}")

    def update_connection_status(self, message: str, color: str = "black"):
        """Update connection status"""
        try:
            self.connection_status.set(message)
            # Find the label and update its color
            for child in self.root.winfo_children():
                for grandchild in child.winfo_children():
                    if hasattr(grandchild, 'cget'):
                        try:
                            if grandchild.cget('textvariable') == str(self.connection_status):
                                grandchild.configure(foreground=color)
                                break
                        except:
                            continue
        except Exception as e:
            print(f"Error updating connection status: {e}")

    def update_auto_connection_status(self, message: str, color: str = "black"):
        """Update auto-connection status (kept for compatibility)"""
        try:
            # This is now handled by connection_status
            self.update_connection_status(message, color)
        except Exception as e:
            print(f"Error updating auto-connection status: {e}")

    def show_info(self, title: str, message: str):
        """Show info message dialog"""
        messagebox.showinfo(title, message)

    def show_error(self, title: str, message: str):
        """Show error message dialog"""
        messagebox.showerror(title, message)

    def show_warning(self, title: str, message: str):
        """Show warning message dialog"""
        messagebox.showwarning(title, message)

    def update_network_info(self, network_info: dict):
        """Update network information display (kept for compatibility)"""
        # This method is kept for compatibility but not actively used
        pass

    def update_status(self, status: str):
        """Update status (kept for compatibility)"""
        # This method is kept for compatibility but not actively used
        pass

    def get_wifi_settings(self) -> tuple:
        """Get WiFi IP and port settings"""
        return self.ip_entry.get().strip(), self.port_entry.get().strip()
