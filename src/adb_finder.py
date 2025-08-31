import subprocess
import os
import platform

class ADBFinder:
    """Finds and validates ADB (Android Debug Bridge) installation"""
    
    @staticmethod
    def find_adb() -> str:
        """Find ADB executable path"""
        # Common ADB locations based on platform
        possible_paths = ADBFinder._get_platform_paths()
        
        for path in possible_paths:
            if ADBFinder._is_valid_adb(path):
                return path
        
        return None
    
    @staticmethod
    def _get_platform_paths() -> list:
        """Get platform-specific ADB paths"""
        system = platform.system().lower()
        
        if system == "windows":
            return [
                "adb",  # If in PATH
                os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools\adb.exe"),
                r"C:\Android\Sdk\platform-tools\adb.exe",
                r"C:\Program Files\Android\Android Studio\Sdk\platform-tools\adb.exe",
                r"C:\Program Files (x86)\Android\Android Studio\Sdk\platform-tools\adb.exe"
            ]
        elif system == "darwin":  # macOS
            return [
                "adb",  # If in PATH
                "/usr/local/bin/adb",
                "/opt/homebrew/bin/adb",
                os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
                "/Applications/Android Studio.app/Contents/sdk/platform-tools/adb"
            ]
        else:  # Linux and others
            return [
                "adb",  # If in PATH
                "/usr/local/bin/adb",
                "/opt/android-sdk/platform-tools/adb",
                "/usr/bin/adb",
                os.path.expanduser("~/Android/Sdk/platform-tools/adb")
            ]
    
    @staticmethod
    def _is_valid_adb(path: str) -> bool:
        """Check if the given path is a valid ADB executable"""
        try:
            if not path:
                return False
            
            # Check if file exists (for absolute paths)
            if os.path.isabs(path) and not os.path.isfile(path):
                return False
            
            # Try to run ADB version command
            result = subprocess.run([path, "version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            return result.returncode == 0 and "Android Debug Bridge" in result.stdout
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, PermissionError):
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_adb_version(adb_path: str) -> str:
        """Get ADB version string"""
        try:
            result = subprocess.run([adb_path, "version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('Android Debug Bridge'):
                        return line.strip()
            
            return "Unknown version"
            
        except Exception as e:
            return f"Error getting version: {str(e)}"
    
    @staticmethod
    def test_adb_connection(adb_path: str) -> bool:
        """Test if ADB can start and communicate"""
        try:
            # Kill any existing ADB server
            subprocess.run([adb_path, "kill-server"], 
                         capture_output=True, 
                         timeout=5)
            
            # Start ADB server
            result = subprocess.run([adb_path, "start-server"], 
                                  capture_output=True, 
                                  timeout=10)
            
            if result.returncode == 0:
                # Test basic ADB command
                test_result = subprocess.run([adb_path, "devices"], 
                                           capture_output=True, 
                                           timeout=10)
                return test_result.returncode == 0
            
            return False
            
        except Exception:
            return False
    
    @staticmethod
    def get_installation_instructions() -> str:
        """Get platform-specific installation instructions"""
        system = platform.system().lower()
        
        if system == "windows":
            return """
Windows Installation:
1. Download Android SDK Platform Tools from: https://developer.android.com/studio/releases/platform-tools
2. Extract the ZIP file to a folder (e.g., C:\\Android\\Sdk\\platform-tools)
3. Add the folder to your system PATH:
   - Right-click 'This PC' → Properties → Advanced system settings
   - Click 'Environment Variables'
   - Under 'System variables', find 'Path' and click 'Edit'
   - Click 'New' and add the platform-tools folder path
   - Click 'OK' on all dialogs
4. Restart your command prompt/terminal
5. Test by running: adb version
            """
        elif system == "darwin":  # macOS
            return """
macOS Installation:
Option 1 - Using Homebrew (recommended):
1. Install Homebrew if not already installed: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
2. Run: brew install android-platform-tools
3. Test by running: adb version

Option 2 - Manual installation:
1. Download Android SDK Platform Tools from: https://developer.android.com/studio/releases/platform-tools
2. Extract and move to /usr/local/bin/
3. Test by running: adb version
            """
        else:  # Linux
            return """
Linux Installation:
Option 1 - Using package manager:
Ubuntu/Debian: sudo apt-get install android-tools-adb
Fedora: sudo dnf install android-tools
Arch: sudo pacman -S android-tools

Option 2 - Manual installation:
1. Download Android SDK Platform Tools from: https://developer.android.com/studio/releases/platform-tools
2. Extract to /opt/android-sdk/platform-tools/
3. Add to PATH: export PATH=$PATH:/opt/android-sdk/platform-tools
4. Test by running: adb version
            """
