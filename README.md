# 🔌 ADB Connector - Smart Device Bridge

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Professional Android Debug Bridge (ADB) connection tool with automatic device detection and smart WiFi bridging**

## 🌟 **Features**

- ✅ **Automatic Device Detection** - No manual scanning needed
- ✅ **Smart WiFi Auto-Connection** - Automatically switches from USB to WiFi
- ✅ **Device Information Display** - Shows device name, model, battery, and more
- ✅ **TCP/IP Management** - Restart TCP/IP for troubleshooting
- ✅ **Real-time Status Updates** - Live connection progress monitoring
- ✅ **Compact Modern UI** - Clean, professional interface
- ✅ **Cross-Platform Support** - Works on Windows 10/11

## 🚀 **Quick Start**

### **Download & Run**
1. Download `ADB_Connector.exe` from [Releases](../../releases)
2. Double-click to run (No Python installation required!)
3. Connect your Android device via USB
4. Enable USB debugging on your phone
5. Watch the magic happen! ✨

### **Requirements**
- **Windows 10/11** (64-bit)
- **ADB (Android Debug Bridge)** - [Download here](https://developer.android.com/studio/releases/platform-tools)
- **Android device** with USB debugging enabled

## 📱 **How It Works**

### **1. USB Connection**
```
Phone (USB) → PC → ADB Connector → Device Detected
```

### **2. WiFi Bridge Setup**
```
Device Info → WiFi IP Detection → Network Check → Auto-Connect
```

### **3. Seamless Transition**
```
USB Connected → WiFi IP Found → WiFi Connected → USB Disconnected
```

## 🔧 **Setup Instructions**

### **Install ADB**
1. Download [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
2. Extract to `C:\platform-tools`
3. Add to system PATH: `C:\platform-tools`
4. Restart your computer

### **Enable USB Debugging**
1. Go to **Settings > About Phone**
2. Tap **Build Number** 7 times
3. Go to **Settings > Developer Options**
4. Enable **USB Debugging**
5. Enable **WiFi Debugging**

## 🎯 **Usage Guide**

### **Basic Connection**
1. **Connect phone via USB**
2. **Tool automatically detects** your device
3. **Shows device information** (name, model, battery)
4. **Automatically attempts WiFi connection**
5. **Disconnect USB** - device stays connected via WiFi

### **Advanced Features**
- **TCP/IP Restart**: Troubleshoot WiFi connection issues
- **Device Details**: Expand to see comprehensive device information
- **Real-time Logs**: Monitor connection progress and status
- **Smart Fallback**: Keeps USB connection if WiFi fails

## 🏗️ **Development**

### **Prerequisites**
```bash
Python 3.13+
pip install -r requirements.txt
```

### **Run from Source**
```bash
python main.py
```

### **Build Executable**
```bash
# Using batch file
build_exe.bat

# Or manually
pyinstaller --onefile --windowed --name "ADB_Connector" main.py
```

## 📁 **Project Structure**

```
ADB_connector/
├── main.py                 # Main application entry point
├── src/                    # Source code modules
│   ├── gui_manager.py     # GUI management and interface
│   ├── device_manager.py  # ADB device operations
│   ├── connection_manager.py # Connection handling
│   └── network_detector.py # Network detection
├── dist/                   # Built executables
│   └── ADB_Connector.exe  # Standalone executable
├── build_exe.bat          # Build script for Windows
└── requirements.txt        # Python dependencies
```

## 🔍 **Troubleshooting**

### **Common Issues**

| Problem | Solution |
|---------|----------|
| "ADB not found" | Install Android SDK Platform Tools and add to PATH |
| Device not detected | Check USB cable, enable USB debugging, install drivers |
| WiFi connection fails | Use "Restart TCP/IP" button, check network compatibility |
| App crashes | Ensure ADB is properly installed and in PATH |

### **Debug Mode**
Run from source with console output:
```bash
python main.py
```

## 📊 **Technical Details**

- **Language**: Python 3.13
- **GUI Framework**: Tkinter
- **Packaging**: PyInstaller
- **Architecture**: Modular design with separation of concerns
- **Dependencies**: Standard library modules only

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Android Debug Bridge (ADB)** - Google's ADB tool
- **PyInstaller** - Python packaging tool
- **Tkinter** - Python GUI framework

## 📞 **Support**

- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)
- **Wiki**: [Project Wiki](../../wiki)

---

**Made with ❤️ by [yasirSub](https://github.com/yasirSub)**

*Star this repository if it helped you! ⭐*
