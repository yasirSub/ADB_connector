import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time
import os
import threading
import winreg

# Optional system tray support
try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None
    Image = None
    ImageDraw = None

class GUIManager:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB Connector - Smart Device Bridge")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        # Beautiful modern color scheme with gradients
        self.colors = {
            'primary': '#667eea',       # Beautiful blue-purple gradient start
            'primary_dark': '#764ba2',  # Beautiful blue-purple gradient end
            'secondary': '#f093fb',     # Pink gradient start
            'secondary_dark': '#f5576c', # Pink gradient end
            'success': '#4facfe',       # Blue gradient start
            'success_dark': '#00f2fe',  # Blue gradient end
            'success_green': '#43e97b', # Green gradient start
            'success_green_dark': '#38f9d7', # Green gradient end
            'danger': '#fa709a',        # Pink-red gradient start
            'danger_dark': '#fee140',   # Pink-red gradient end
            'warning': '#ffecd2',       # Orange gradient start
            'warning_dark': '#fcb69f',  # Orange gradient end
            'info': '#a8edea',          # Cyan gradient start
            'info_dark': '#fed6e3',     # Cyan gradient end
            'dark': '#2c3e50',          # Modern dark blue
            'light': '#f8f9fa',         # Clean light gray
            'white': '#FFFFFF',
            'gray': '#6c757d',
            'text_primary': '#2c3e50',   # Modern dark text
            'text_secondary': '#6c757d', # Medium gray text
            'glossy_blue': '#667eea',    # Modern blue
            'glossy_gray': '#f8f9fa',    # Clean light gray
            'accent': '#ff6b6b',         # Beautiful accent red
            'accent_blue': '#4ecdc4',    # Beautiful accent teal
            'background': '#f8f9fa',     # Clean background
            'card_bg': '#ffffff',        # Card background
            'border': '#e9ecef'          # Subtle border
        }
        
        # Set beautiful background
        self.root.configure(bg=self.colors['background'])
        
        # Configure modern styling
        self._configure_styles()
        
        # App icon path (project root: icon.png)
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            self.app_icon_path = os.path.join(project_root, 'icon.png')
        except Exception:
            self.app_icon_path = None
        
        # Tray icon state
        self.tray_icon = None
        self._tray_thread = None
        
        # Callback functions
        self.on_connect_usb = None
        self.on_connect_wifi = None
        self.on_disconnect = None
        self.on_restart_tcpip = None
        
        # Create the main interface
        self._create_main_interface()
        
        # Bind device selection event
        self.device_listbox.bind('<<ListboxSelect>>', self._on_device_selection)

        # Initialize system tray (if supported)
        self._init_tray()

        # Apply window icon from icon.png if available
        try:
            if self.app_icon_path and os.path.exists(self.app_icon_path):
                icon_img = tk.PhotoImage(file=self.app_icon_path)
                self.root.iconphoto(True, icon_img)
                # Keep a reference to avoid garbage collection
                self._tk_icon_image_ref = icon_img
        except Exception:
            pass

        # Minimize-to-tray: hide when minimized, restore from tray menu
        try:
            self.root.bind('<Unmap>', self._on_window_unmap)
        except Exception:
            pass
        
        # Show welcome dialog on first run
        self._check_first_run()

    def _configure_styles(self):
        """Configure modern ttk styles"""
        try:
            style = ttk.Style()
            
            # Configure beautiful modern button styles with black text
            style.configure('Primary.TButton',
                          background=self.colors['primary'],
                          foreground='#000000',
                          font=('Segoe UI', 9, 'bold'),
                          padding=(12, 8),
                          relief='flat',
                          borderwidth=0,
                          focuscolor='none')
            
            style.configure('Success.TButton',
                          background=self.colors['success_green'],
                          foreground='#000000',
                          font=('Segoe UI', 9, 'bold'),
                          padding=(12, 8),
                          relief='flat',
                          borderwidth=0,
                          focuscolor='none')
            
            style.configure('Danger.TButton',
                          background=self.colors['danger'],
                          foreground='#000000',
                          font=('Segoe UI', 9, 'bold'),
                          padding=(12, 8),
                          relief='flat',
                          borderwidth=0,
                          focuscolor='none')
            
            style.configure('Info.TButton',
                          background=self.colors['accent_blue'],
                          foreground='#000000',
                          font=('Segoe UI', 9, 'bold'),
                          padding=(12, 8),
                          relief='flat',
                          borderwidth=0,
                          focuscolor='none')
            
            # Add hover effects
            style.map('Primary.TButton',
                     background=[('active', self.colors['primary_dark'])])
            style.map('Success.TButton',
                     background=[('active', self.colors['success_green_dark'])])
            style.map('Danger.TButton',
                     background=[('active', self.colors['danger_dark'])])
            style.map('Info.TButton',
                     background=[('active', self.colors['info_dark'])])
            
            # Configure beautiful modern frame styles
            style.configure('Card.TFrame',
                          background=self.colors['card_bg'],
                          relief='flat',
                          borderwidth=0)
            
            style.configure('Header.TFrame',
                          background=self.colors['primary'],
                          relief='flat')
            
            style.configure('Glossy.TFrame',
                          background=self.colors['card_bg'],
                          relief='flat',
                          borderwidth=0)
            
            # Configure beautiful modern label styles
            style.configure('Title.TLabel',
                          background=self.colors['primary'],
                          foreground='#ffffff',
                          font=('Segoe UI', 14, 'bold'))
            
            style.configure('Subtitle.TLabel',
                          background=self.colors['primary'],
                          foreground='#ffffff',
                          font=('Segoe UI', 10, 'normal'))
            
            style.configure('Status.TLabel',
                          background=self.colors['card_bg'],
                          foreground=self.colors['text_primary'],
                          font=('Segoe UI', 9, 'bold'))
            
            style.configure('Info.TLabel',
                          background=self.colors['card_bg'],
                          foreground=self.colors['text_secondary'],
                          font=('Segoe UI', 9))
            
            # Configure beautiful modern entry styles
            style.configure('Modern.TEntry',
                          fieldbackground=self.colors['white'],
                          borderwidth=1,
                          relief='solid',
                          font=('Segoe UI', 9),
                          bordercolor=self.colors['border'])
            
            # Configure beautiful modern labelframe styles
            style.configure('Glossy.TLabelframe',
                          background=self.colors['card_bg'],
                          relief='flat',
                          borderwidth=1,
                          bordercolor=self.colors['border'])
            
            style.configure('Glossy.TLabelframe.Label',
                          background=self.colors['card_bg'],
                          foreground=self.colors['text_primary'],
                          font=('Segoe UI', 10, 'bold'))
            
        except Exception as e:
            print(f"Error configuring styles: {e}")

    def _create_main_interface(self):
        """Create the main interface"""
        # Create a canvas and scrollbar for scrollable content
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main frame with beautiful modern padding
        main_frame = ttk.Frame(scrollable_frame, padding="15", style='Card.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        
        # Bind mousewheel to canvas for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store canvas reference for cleanup
        self._canvas = canvas
        
        # Bind window close to cleanup
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Beautiful header section with modern styling
        header_frame = ttk.Frame(main_frame, style='Header.TFrame', padding="20")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        # Title with beautiful modern styling
        title_label = ttk.Label(header_frame, text="📱 ADB Connector", style='Title.TLabel')
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(header_frame, text="Smart Device Bridge", style='Subtitle.TLabel')
        subtitle_label.pack()
        
        # About button in header
        about_btn = ttk.Button(header_frame, text="ℹ️ About", 
                              command=self._show_about, style='Info.TButton')
        about_btn.pack(pady=(5, 0))
        
        # Device List Frame with premium glossy styling
        device_frame = ttk.LabelFrame(main_frame, text="📱 Connected Devices", padding="15", style='Glossy.TLabelframe')
        device_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 15))
        device_frame.columnconfigure(1, weight=1)
        
        # Device listbox with scrollbar
        listbox_frame = ttk.Frame(device_frame)
        listbox_frame.grid(row=0, column=0, sticky="ew")
        listbox_frame.columnconfigure(0, weight=1)
        
        self.device_listbox = tk.Listbox(listbox_frame, height=3, selectmode=tk.SINGLE, 
                                        font=('Segoe UI', 9), 
                                        foreground=self.colors['text_primary'], 
                                        bg=self.colors['white'],
                                        selectbackground=self.colors['primary'],
                                        selectforeground='#ffffff',
                                        borderwidth=1,
                                        relief='solid')
        self.device_listbox.grid(row=0, column=0, sticky="ew")
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.device_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.device_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Beautiful device action buttons with modern styling
        button_frame = ttk.Frame(device_frame)
        button_frame.grid(row=1, column=0, pady=(10, 0))
        
        self.connect_usb_btn = ttk.Button(button_frame, text="🔌 Connect USB", 
                                         command=self._on_connect_usb_clicked, style='Primary.TButton')
        self.connect_usb_btn.grid(row=0, column=0, padx=(0, 8))
        
        self.disconnect_btn = ttk.Button(button_frame, text="❌ Disconnect", 
                                        command=self._on_disconnect_clicked, style='Danger.TButton')
        self.disconnect_btn.grid(row=0, column=1, padx=(0, 8))
        
        # Expandable device info section
        self.expand_button = ttk.Button(button_frame, text=">> Show Details", 
                                       command=self._toggle_device_details, style='Info.TButton')
        self.expand_button.grid(row=0, column=2)
        
        # Device info display (basic) with glossy styling
        self.device_info_frame = ttk.LabelFrame(device_frame, text="Device Information", padding="3", style='Glossy.TLabelframe')
        self.device_info_frame.grid(row=2, column=0, sticky="ew", pady=(3, 0))
        
        # Basic device info labels
        self.device_info_labels = {}
        self._create_device_info_labels()
        
        # Logging optimization - track recent messages to avoid spam
        self.recent_logs = []
        self.max_recent_logs = 10
        
        # Detailed device info frame (initially hidden)
        self.detailed_info_frame = ttk.Frame(self.device_info_frame)
        self.detailed_info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        self.detailed_info_frame.grid_remove()  # Hide initially
        
        # Detailed device info labels
        self.detailed_info_labels = {}
        self._create_detailed_device_info_labels()
        
        # Beautiful WiFi Connection Frame with modern styling
        wifi_frame = ttk.LabelFrame(main_frame, text="🌐 WiFi Connection", padding="15", style='Glossy.TLabelframe')
        wifi_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=(0, 15))
        wifi_frame.columnconfigure(1, weight=1)
        
        # Beautiful IP and Port inputs with modern styling
        ttk.Label(wifi_frame, text="IP Address:", font=('Segoe UI', 9, 'bold'), foreground=self.colors['text_primary']).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.ip_entry = ttk.Entry(wifi_frame, width=18, style='Modern.TEntry', font=('Segoe UI', 9))
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        self.ip_entry.insert(0, "192.168.1.100")
        
        ttk.Label(wifi_frame, text="Port:", font=('Segoe UI', 9, 'bold'), foreground=self.colors['text_primary']).grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.port_entry = ttk.Entry(wifi_frame, width=8, style='Modern.TEntry', font=('Segoe UI', 9))
        self.port_entry.grid(row=0, column=3, sticky="w", padx=(0, 10))
        self.port_entry.insert(0, "5555")
        
        # WiFi action buttons with modern styling
        self.wifi_connect_button = ttk.Button(wifi_frame, text="🔗 Connect WiFi", 
                                             command=self._on_connect_wifi_clicked, style='Success.TButton')
        self.wifi_connect_button.grid(row=0, column=4, padx=(0, 10))
        
        self.restart_tcpip_button = ttk.Button(wifi_frame, text="🔄 Restart TCP/IP", 
                                              command=self._on_restart_tcpip_clicked, style='Info.TButton')
        self.restart_tcpip_button.grid(row=0, column=5)
        
        # WiFi setup help button with modern styling
        self.wifi_setup_button = ttk.Button(wifi_frame, text="📱 WiFi Setup Guide", 
                                           command=self._show_wifi_setup, style='Info.TButton')
        self.wifi_setup_button.grid(row=1, column=0, columnspan=6, pady=(5, 0), sticky="ew")
        
        # Beautiful Status Frame with modern styling
        status_frame = ttk.LabelFrame(main_frame, text="📊 Status", padding="15", style='Glossy.TLabelframe')
        status_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 15))
        status_frame.columnconfigure(0, weight=1)
        
        # Status indicators with modern styling
        status_row = ttk.Frame(status_frame)
        status_row.grid(row=0, column=0, sticky="ew")
        status_row.columnconfigure(1, weight=1)
        
        # Connection status indicators with visual indicators
        status_indicator_frame = ttk.Frame(status_row)
        status_indicator_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        status_indicator_frame.columnconfigure(1, weight=1)
        
        # Monitoring status with indicator
        self.monitoring_indicator = tk.Label(status_indicator_frame, text="●", font=('Arial', 12), foreground='#FF9800')
        self.monitoring_indicator.grid(row=0, column=0, sticky="w", padx=(0, 5))
        ttk.Label(status_indicator_frame, text="Monitoring:", font=('Arial', 9, 'bold'), foreground='#000000').grid(row=0, column=1, sticky="w", padx=(0, 5))
        self.monitoring_status = tk.StringVar(value="Searching for devices...")
        monitoring_label = ttk.Label(status_indicator_frame, textvariable=self.monitoring_status, foreground='#000000', font=('Arial', 9))
        monitoring_label.grid(row=0, column=2, sticky="w")
        
        # Connection status with indicator
        self.connection_indicator = tk.Label(status_indicator_frame, text="●", font=('Arial', 12), foreground='#9E9E9E')
        self.connection_indicator.grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(3, 0))
        ttk.Label(status_indicator_frame, text="Connection:", font=('Arial', 9, 'bold'), foreground='#000000').grid(row=1, column=1, sticky="w", padx=(0, 5), pady=(3, 0))
        self.connection_status = tk.StringVar(value="Ready to connect")
        connection_label = ttk.Label(status_indicator_frame, textvariable=self.connection_status, foreground='#000000', font=('Arial', 9))
        connection_label.grid(row=1, column=2, sticky="w", pady=(3, 0))
        
        # Beautiful Log Frame with modern styling
        log_frame = ttk.LabelFrame(main_frame, text="📝 Activity Log", padding="15", style='Glossy.TLabelframe')
        log_frame.grid(row=4, column=0, sticky="ew", padx=0, pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text widget with scrollbar
        log_widget_frame = ttk.Frame(log_frame)
        log_widget_frame.grid(row=0, column=0, sticky="nsew")
        log_widget_frame.columnconfigure(0, weight=1)
        log_widget_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_widget_frame, height=5, wrap=tk.WORD, state=tk.DISABLED, 
                               foreground=self.colors['text_primary'], 
                               bg=self.colors['white'],
                               font=('Segoe UI', 9),
                               borderwidth=1,
                               relief='solid')
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        log_scrollbar = ttk.Scrollbar(log_widget_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Clear log button with modern styling
        clear_log_btn = ttk.Button(log_frame, text="🗑️ Clear Log", command=self._clear_log, style='Danger.TButton')
        clear_log_btn.grid(row=1, column=0, pady=(10, 0), sticky="w")
        


    def _create_device_info_labels(self):
        """Create basic device info labels"""
        info_frame = ttk.Frame(self.device_info_frame)
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        info_frame.columnconfigure(1, weight=1)
        
        # Basic info labels
        labels = ['device_id', 'status', 'connection_type', 'pc_ip']
        for i, label in enumerate(labels):
            ttk.Label(info_frame, text=f"{label.replace('_', ' ').title()}:", font=("Arial", 9, "bold"), foreground='#000000').grid(row=i, column=0, sticky="w", padx=(0, 10), pady=2)
            label_widget = ttk.Label(info_frame, text="Not connected", foreground='#000000', font=("Arial", 9))
            label_widget.grid(row=i, column=1, sticky="w", pady=2)
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
            label_widget = ttk.Label(self.detailed_info_frame, text="N/A", foreground="#000000")
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

    def _show_about(self):
        """Show About dialog with author info and GitHub repo"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About ADB Connector")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        
        # Make window modal
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Content
        content_frame = ttk.Frame(about_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(content_frame, text="🔌 ADB Connector", font=("Arial", 16, "bold"))
        title.pack(pady=(0, 10))
        
        # Subtitle
        subtitle = ttk.Label(content_frame, text="Smart Device Bridge", font=("Arial", 12))
        subtitle.pack(pady=(0, 20))
        
        # Author info
        author_frame = ttk.Frame(content_frame)
        author_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(author_frame, text="Created by:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(author_frame, text="Yasir Subhani", font=("Arial", 12)).pack(anchor=tk.W, pady=(5, 0))
        
        # GitHub repo
        repo_frame = ttk.Frame(content_frame)
        repo_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(repo_frame, text="GitHub Repository:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Make GitHub link clickable
        github_text = "https://github.com/yasirSub"
        github_label = ttk.Label(repo_frame, text=github_text, font=("Arial", 10), foreground="#000000", cursor="hand2")
        github_label.pack(anchor=tk.W, pady=(5, 0))
        github_label.bind("<Button-1>", lambda e: self._open_github())
        
        # Description
        desc_frame = ttk.Frame(content_frame)
        desc_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(desc_frame, text="Description:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        description = """A powerful tool for connecting Android devices via USB and WiFi.
Features automatic device detection, network scanning, and system tray integration.
Perfect for developers and power users who need reliable ADB connections."""
        
        desc_text = tk.Text(desc_frame, height=4, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 9))
        desc_text.pack(fill=tk.X, pady=(5, 0))
        desc_text.configure(state=tk.NORMAL)
        desc_text.insert(tk.END, description)
        desc_text.configure(state=tk.DISABLED)
        
        # Startup options
        startup_frame = ttk.LabelFrame(content_frame, text="🚀 Windows Startup", padding="10")
        startup_frame.pack(fill=tk.X, pady=(0, 20))
        
        startup_status = self._check_startup_status()
        startup_text = "✅ Enabled" if startup_status else "❌ Disabled"
        
        ttk.Label(startup_frame, text=f"Status: {startup_text}", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        if startup_status:
            disable_btn = ttk.Button(startup_frame, text="Disable Startup", 
                                   command=lambda: [self._disable_startup(), about_window.destroy()])
            disable_btn.pack(anchor=tk.W, pady=(5, 0))
        else:
            enable_btn = ttk.Button(startup_frame, text="Enable Startup", 
                                  command=lambda: [self._enable_startup(), about_window.destroy()])
            enable_btn.pack(anchor=tk.W, pady=(5, 0))
        
        # Version info
        version_frame = ttk.Frame(content_frame)
        version_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(version_frame, text="Version: 1.0.0", font=("Arial", 9)).pack(anchor=tk.W)
        ttk.Label(version_frame, text="Python 3.7+ • Tkinter • ADB", font=("Arial", 9)).pack(anchor=tk.W)
        
        # Close button
        close_btn = ttk.Button(content_frame, text="Close", command=about_window.destroy)
        close_btn.pack(pady=(10, 0))
        
        # Center dialog
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (about_window.winfo_width() // 2)
        y = (about_window.winfo_screenheight() // 2) - (about_window.winfo_height() // 2)
        about_window.geometry(f"+{x}+{y}")

    def _open_github(self):
        """Open GitHub repository in default browser"""
        import webbrowser
        try:
            webbrowser.open("https://github.com/yasirSub")
        except Exception as e:
            print(f"Error opening GitHub: {e}")

    def _check_first_run(self):
        """Check if this is the first run and show welcome dialog"""
        import os
        import json
        
        config_file = os.path.join(os.path.dirname(__file__), '..', 'first_run.json')
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                if config.get('first_run_completed', False):
                    return  # Not first run
            else:
                # First run - show welcome dialog
                self._show_welcome_dialog()
                
                # Mark first run as completed
                config = {'first_run_completed': True}
                with open(config_file, 'w') as f:
                    json.dump(config, f)
                    
        except Exception as e:
            print(f"Error checking first run: {e}")

    def _show_welcome_dialog(self):
        """Show welcome dialog for first-time users"""
        welcome_window = tk.Toplevel(self.root)
        welcome_window.title("Welcome to ADB Connector!")
        welcome_window.geometry("600x500")
        welcome_window.resizable(False, False)
        
        # Make window modal and center it
        welcome_window.transient(self.root)
        welcome_window.grab_set()
        
        # Content
        content_frame = ttk.Frame(welcome_window, padding="30")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome title
        title = ttk.Label(content_frame, text="🎉 Welcome to ADB Connector!", font=("Arial", 18, "bold"))
        title.pack(pady=(0, 20))
        
        # Author credit
        author_frame = ttk.Frame(content_frame)
        author_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(author_frame, text="Created by Yasir Subhani", font=("Arial", 14, "bold")).pack()
        ttk.Label(author_frame, text="A powerful tool for Android device connections", font=("Arial", 12)).pack(pady=(5, 0))
        
        # GitHub section
        github_frame = ttk.LabelFrame(content_frame, text="📂 GitHub Repository", padding="15")
        github_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(github_frame, text="Visit the project on GitHub:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        github_text = "https://github.com/yasirSub"
        github_label = ttk.Label(github_frame, text=github_text, font=("Arial", 11), foreground="#000000", cursor="hand2")
        github_label.pack(anchor=tk.W, pady=(5, 10))
        github_label.bind("<Button-1>", lambda e: self._open_github())
        
        # Features
        features_frame = ttk.LabelFrame(content_frame, text="✨ Features", padding="15")
        features_frame.pack(fill=tk.X, pady=(0, 20))
        
        features = [
            "🔌 USB and WiFi device connections",
            "📱 Automatic device detection",
            "🌐 Network scanning and auto-connection",
            "📊 Real-time device monitoring",
            "🔔 System tray integration",
            "📝 Detailed device information"
        ]
        
        for feature in features:
            ttk.Label(features_frame, text=feature, font=("Arial", 10)).pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        github_btn = ttk.Button(button_frame, text="🌐 Open GitHub", command=self._open_github)
        github_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        about_btn = ttk.Button(button_frame, text="ℹ️ About", command=lambda: [welcome_window.destroy(), self._show_about()])
        about_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        start_btn = ttk.Button(button_frame, text="🚀 Get Started", command=welcome_window.destroy)
        start_btn.pack(side=tk.RIGHT)
        
        # Center dialog
        welcome_window.update_idletasks()
        x = (welcome_window.winfo_screenwidth() // 2) - (welcome_window.winfo_width() // 2)
        y = (welcome_window.winfo_screenheight() // 2) - (welcome_window.winfo_height() // 2)
        welcome_window.geometry(f"+{x}+{y}")

    def _enable_startup(self):
        """Enable Windows startup for the application"""
        try:
            # Get the path to the current executable
            exe_path = os.path.abspath("dist/ADB_Connector.exe")
            if not os.path.exists(exe_path):
                exe_path = os.path.abspath("main.py")
            
            # Add to Windows startup registry
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "ADB_Connector", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            
            self.log_message("✅ Added to Windows startup")
            messagebox.showinfo("Startup Enabled", 
                              "ADB Connector has been added to Windows startup!\n\n"
                              "The app will now start automatically when you log in.")
        except Exception as e:
            self.log_message(f"❌ Failed to enable startup: {str(e)}")
            messagebox.showerror("Startup Error", 
                               f"Failed to add to Windows startup:\n{str(e)}")
    
    def _disable_startup(self):
        """Disable Windows startup for the application"""
        try:
            # Remove from Windows startup registry
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "ADB_Connector")
            winreg.CloseKey(key)
            
            self.log_message("✅ Removed from Windows startup")
            messagebox.showinfo("Startup Disabled", 
                              "ADB Connector has been removed from Windows startup.")
        except Exception as e:
            self.log_message(f"❌ Failed to disable startup: {str(e)}")
            messagebox.showerror("Startup Error", 
                               f"Failed to remove from Windows startup:\n{str(e)}")
    
    def _check_startup_status(self):
        """Check if the application is set to start with Windows"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "ADB_Connector")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def _on_closing(self):
        """Handle window closing - cleanup and exit"""
        try:
            # Unbind mousewheel to prevent memory leaks
            if hasattr(self, '_canvas'):
                self._canvas.unbind_all("<MouseWheel>")
            
            # Stop tray icon if running
            if self.tray_icon:
                self.tray_icon.visible = False
                self.tray_icon.stop()
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.root.destroy()

    def _clear_log(self):
        """Clear the log text"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # ----------------------
    # System tray management
    # ----------------------
    def _init_tray(self):
        """Initialize system tray icon if dependencies are available."""
        if not pystray:
            return
        try:
            image = self._create_tray_image()
            menu = pystray.Menu(
                pystray.MenuItem('Show Window', self._tray_show_window),
                pystray.MenuItem('Hide Window', self._tray_hide_window),
                pystray.MenuItem('Exit', self._tray_exit)
            )
            self.tray_icon = pystray.Icon("adb_connector", image, "📱 ADB: Ready", menu)

            # Run tray in a background thread so it doesn't block Tk
            def run_tray():
                try:
                    self.tray_icon.run()
                except Exception:
                    pass
            self._tray_thread = threading.Thread(target=run_tray, daemon=True)
            self._tray_thread.start()
        except Exception:
            self.tray_icon = None

    def _create_tray_image(self):
        """Create or load the tray icon image (prefer icon.png)."""
        try:
            if Image is None:
                return None
            # Prefer provided icon.png
            if getattr(self, 'app_icon_path', None) and os.path.exists(self.app_icon_path):
                return Image.open(self.app_icon_path)
            # Fallback: generate simple glyph
            if ImageDraw is None:
                return None
            size = 64
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse((4, 4, size-4, size-4), fill=(52, 152, 219, 255))
            draw.rectangle((24, 16, 40, 48), fill=(255, 255, 255, 255))
            draw.rectangle((28, 48, 36, 52), fill=(255, 255, 255, 255))
            return image
        except Exception:
            return None

    def _tray_show_window(self, icon, item):
        try:
            self.root.after(0, self.root.deiconify)
        except Exception:
            pass

    def _tray_hide_window(self, icon, item):
        try:
            self.root.after(0, self.root.withdraw)
        except Exception:
            pass

    def _tray_exit(self, icon, item):
        try:
            if self.tray_icon:
                self.tray_icon.visible = False
                self.tray_icon.stop()
        finally:
            self.root.after(0, self.root.quit)

    def _update_tray_title(self, title: str):
        """Update tray tooltip/title with current connection info."""
        try:
            if self.tray_icon and hasattr(self.tray_icon, 'title'):
                self.tray_icon.title = title
                print(f"Tray updated: {title}")  # Debug log
        except Exception as e:
            print(f"Error updating tray title: {e}")

    def update_tray_device_status(self, device_name: str = None, connection_type: str = None, status: str = None):
        """Manually update tray with device status"""
        try:
            if device_name and status and status.lower() in ['connected', 'device']:
                tray_text = f"📱 {device_name} ({connection_type or 'USB'})"
            elif device_name:
                tray_text = f"📱 {device_name} - {status or 'Ready'}"
            else:
                tray_text = "📱 ADB Connector - Ready"
            
            self._update_tray_title(tray_text)
        except Exception as e:
            print(f"Error updating tray device status: {e}")

    def _on_window_unmap(self, event):
        """When the window is minimized, hide it to the system tray."""
        try:
            # Only act on minimize/iconify, not on withdraw we trigger ourselves
            if self.root.state() == 'iconic':
                self.root.withdraw()
                # Optionally update tray title to indicate hidden
                self._update_tray_title("📱 Hidden to tray")
        except Exception:
            pass

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

    def update_device_info(self, device_info: dict, pc_ip: str = None):
        """Update device information display. Accepts optional pc_ip for compatibility."""
        try:
            data = device_info or {}
            if pc_ip is not None:
                data = dict(data)
                data['pc_ip'] = pc_ip
            for key, label in self.device_info_labels.items():
                if key in data:
                    value = data[key] or "N/A"
                    label.configure(text=str(value), foreground="#000000")
                else:
                    label.configure(text="N/A", foreground="#000000")

            # Update tray with device name and connection info
            device_name = data.get('device_name') or data.get('device_id') or data.get('device_ip') or 'No Device'
            connection = data.get('connection_type') or 'N/A'
            status = data.get('status') or 'N/A'
            
            # Create a clear tooltip showing connected device
            if device_name != 'No Device' and status.lower() in ['connected', 'device']:
                # Show device name prominently
                if data.get('device_name') and data.get('device_name') != 'Unknown Device':
                    tray_text = f"📱 {data.get('device_name')} ({connection})"
                else:
                    tray_text = f"📱 {device_name} ({connection})"
            else:
                tray_text = f"📱 ADB Connector - Ready"
            
            self._update_tray_title(tray_text)
        except Exception as e:
            print(f"Error updating device info: {e}")

    def update_detailed_device_info(self, detailed_info: dict):
        """Update detailed device information display"""
        try:
            for key, label in self.detailed_info_labels.items():
                if key in detailed_info:
                    value = detailed_info[key] or "N/A"
                    label.configure(text=str(value), foreground="#000000")
                else:
                    label.configure(text="N/A", foreground="#000000")
            
            # Also update tray with detailed device info
            if detailed_info:
                device_name = detailed_info.get('device_name') or detailed_info.get('device_id') or 'Unknown Device'
                connection = detailed_info.get('connection_type') or 'USB'
                status = detailed_info.get('status') or 'Connected'
                
                if device_name != 'Unknown Device' and status.lower() in ['connected', 'device']:
                    tray_text = f"📱 {device_name} ({connection})"
                else:
                    tray_text = f"📱 ADB Connector - {device_name}"
                
                self._update_tray_title(tray_text)
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
        """Add a message to the log with spam filtering"""
        try:
            # Check for repetitive messages
            message_key = message.split('] ')[-1] if '] ' in message else message  # Remove timestamp for comparison
            
            # Skip if this exact message was logged recently
            if message_key in self.recent_logs:
                return
            
            # Add to recent logs and maintain size
            self.recent_logs.append(message_key)
            if len(self.recent_logs) > self.max_recent_logs:
                self.recent_logs.pop(0)
            
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
        """Update monitoring status with visual indicators"""
        try:
            self.monitoring_status.set(message)
            
            # Update monitoring indicator based on status
            if "Searching" in message or "Scanning" in message:
                self.monitoring_indicator.configure(foreground='#FF9800')  # Orange for searching
            elif "Ready" in message or "Found" in message:
                self.monitoring_indicator.configure(foreground='#4CAF50')  # Green for ready
            elif "Error" in message or "Failed" in message:
                self.monitoring_indicator.configure(foreground='#F44336')  # Red for error
            else:
                self.monitoring_indicator.configure(foreground='#2196F3')  # Blue for other states
            
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
        """Update connection status with visual indicators"""
        try:
            self.connection_status.set(message)
            
            # Update visual indicator based on status
            if "Connected" in message or "connected" in message:
                if "WiFi" in message or "wifi" in message:
                    self.connection_indicator.configure(foreground='#4CAF50')  # Green for WiFi
                else:
                    self.connection_indicator.configure(foreground='#2196F3')  # Blue for USB
            elif "Connecting" in message or "connecting" in message:
                self.connection_indicator.configure(foreground='#FF9800')  # Orange for connecting
            elif "Failed" in message or "failed" in message or "Error" in message:
                self.connection_indicator.configure(foreground='#F44336')  # Red for error
            else:
                self.connection_indicator.configure(foreground='#9E9E9E')  # Gray for ready
            
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
            
            # Reflect in tray title as well - keep it concise
            if "Connected" in message or "connected" in message:
                self._update_tray_title(f"📱 {message}")
            else:
                self._update_tray_title(f"📱 ADB Connector - {message}")
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
