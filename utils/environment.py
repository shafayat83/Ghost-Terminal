r"""
Environment Detector Module
===========================
Detects the operating environment (Windows Native vs WSL) and provides
appropriate path handling and shell command configurations.

WHY THIS MATTERS:
- Windows uses backslashes (\) and drive letters (C:\)
- WSL uses forward slashes (/) and Linux-style paths (/mnt/c/)
- Shell commands differ: PowerShell/CMD vs Bash
- This module ensures Ghost Terminal works seamlessly in both environments
"""

import os
import sys
import platform
from pathlib import Path
from typing import Tuple, Optional


class EnvironmentDetector:
    """
    Detects and provides information about the current execution environment.
    
    Attributes:
        is_windows (bool): True if running on Windows (native or WSL)
        is_wsl (bool): True if running inside Windows Subsystem for Linux
        is_linux (bool): True if running on native Linux
        is_macos (bool): True if running on macOS
    """
    
    def __init__(self):
        """Initialize environment detector and run detection."""
        self.platform_system = platform.system()
        self.platform_release = platform.release()
        
        # Detect WSL by checking for 'microsoft' in platform release or /proc/version
        self.is_wsl = self._detect_wsl()
        
        # Detect operating system
        self.is_windows = self.platform_system == "Windows" and not self.is_wsl
        self.is_linux = self.platform_system == "Linux" and not self.is_wsl
        self.is_macos = self.platform_system == "Darwin"
        
        # Set appropriate shell and path configurations
        self.shell = self._get_default_shell()
        self.path_separator = self._get_path_separator()
        
    def _detect_wsl(self) -> bool:
        """
        Detect if running inside WSL (Windows Subsystem for Linux).
        
        WSL detection methods:
        1. Check platform.release() for 'microsoft' or 'WSL'
        2. Check if /proc/version contains 'microsoft'
        3. Check environment variables set by WSL
        
        Returns:
            bool: True if running in WSL, False otherwise
        """
        # Method 1: Check platform release string
        if self.platform_system == "Linux":
            if 'microsoft' in self.platform_release.lower() or 'wsl' in self.platform_release.lower():
                return True
            
            # Method 2: Check /proc/version (WSL-specific)
            try:
                with open('/proc/version', 'r') as f:
                    proc_version = f.read().lower()
                    if 'microsoft' in proc_version:
                        return True
            except (FileNotFoundError, PermissionError):
                pass  # File doesn't exist or can't be read, not WSL or access denied
            
            # Method 3: Check WSL-specific environment variables
            wsl_env_vars = ['WSL_DISTRO_NAME', 'WSL_INTEROP']
            for var in wsl_env_vars:
                if var in os.environ:
                    return True
        
        return False
    
    def _get_default_shell(self) -> str:
        """
        Determine the default shell for executing commands.
        
        Returns:
            str: Shell executable name (powershell, cmd, bash, sh)
        """
        if self.is_windows:
            # Windows: Prefer PowerShell for modern commands
            return 'powershell'
        elif self.is_wsl or self.is_linux:
            # Linux/WSL: Use bash
            return 'bash'
        elif self.is_macos:
            # macOS: Use bash or sh
            return 'bash'
        else:
            # Fallback
            return 'sh'
    
    def _get_path_separator(self) -> str:
        """
        Get the appropriate path separator for the current environment.
        
        Returns:
            str: Path separator ('\\' for Windows, '/' for Linux/WSL/macOS)
        """
        if self.is_windows:
            return '\\'
        else:
            return '/'
    
    def get_script_extension(self, script_type: str = 'python') -> str:
        """
        Get the appropriate file extension for scripts.
        
        Args:
            script_type: Type of script ('python', 'bash', 'batch')
            
        Returns:
            str: File extension including the dot (e.g., '.py', '.bat', '.sh')
        """
        extensions = {
            'python': '.py',
            'batch': '.bat' if self.is_windows else '.sh',
            'bash': '.sh',
            'powershell': '.ps1'
        }
        return extensions.get(script_type, '.txt')
    
    def convert_path_for_environment(self, path: str) -> str:
        r"""
        Convert a path to be compatible with the current environment.
        
        For WSL: Converts Windows paths (C:\Users) to WSL paths (/mnt/c/Users)
        For Windows: Converts WSL/Linux paths to Windows format
        
        Args:
            path: The path to convert
            
        Returns:
            str: Environment-compatible path
        """
        path_obj = Path(path)
        
        if self.is_wsl:
            # Convert Windows path to WSL path
            path_str = str(path)
            # Handle absolute Windows paths like C:\Users\...
            if len(path_str) >= 2 and path_str[1] == ':':
                drive = path_str[0].lower()
                rest = path_str[2:].replace('\\', '/')
                return f'/mnt/{drive}/{rest}'
            return path_str
            
        elif self.is_windows:
            # Convert WSL path to Windows path
            path_str = str(path)
            # Handle WSL paths like /mnt/c/Users/...
            if path_str.startswith('/mnt/'):
                parts = path_str.split('/')
                if len(parts) >= 3:
                    drive = parts[2].upper()
                    rest = '/'.join(parts[3:])
                    return f'{drive}:\\{rest.replace("/", "\\")}'
            return path_str
        
        # Linux/macOS: no conversion needed
        return str(path_obj)
    
    def get_temp_dir(self) -> Path:
        """
        Get the appropriate temporary directory for scripts.
        
        Returns:
            Path: Path object pointing to the temp scripts directory
        """
        # Get the directory where ghost.py is located
        script_dir = Path(__file__).resolve().parent.parent
        temp_dir = script_dir / 'scripts'
        
        # Create if doesn't exist
        temp_dir.mkdir(exist_ok=True)
        
        return temp_dir
    
    def get_ollama_command(self) -> str:
        """
        Get the appropriate command format for calling Ollama.
        
        Returns:
            str: Shell command template for Ollama API calls
        """
        if self.is_windows:
            # Windows: Use PowerShell Invoke-WebRequest or curl.exe
            return 'curl.exe -s'
        else:
            # Linux/WSL/macOS: Use curl
            return 'curl -s'
    
    def describe_environment(self) -> str:
        """
        Generate a human-readable description of the current environment.
        
        Returns:
            str: Formatted string describing the environment
        """
        env_type = "WSL" if self.is_wsl else (
            "Windows (Native)" if self.is_windows else
            "Linux (Native)" if self.is_linux else
            "macOS" if self.is_macos else
            "Unknown"
        )
        
        return (
            f"Environment: {env_type}\n"
            f"  Platform: {self.platform_system} {self.platform_release}\n"
            f"  Shell: {self.shell}\n"
            f"  Path Separator: '{self.path_separator}'\n"
            f"  Python: {sys.version.split()[0]}"
        )


# Convenience function for quick environment check
def get_environment() -> EnvironmentDetector:
    """
    Create and return an EnvironmentDetector instance.
    
    Returns:
        EnvironmentDetector: Configured detector instance
    """
    return EnvironmentDetector()
