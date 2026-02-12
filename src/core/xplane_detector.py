"""X-Plane installation detection for Windows."""

import os
import winreg
from pathlib import Path
from typing import Optional, List, Tuple


class XPlaneNotFoundError(Exception):
    """Raised when X-Plane installation cannot be found."""
    pass


class XPlaneDetector:
    """Detects X-Plane installation on Windows."""

    # Common installation paths on Windows
    COMMON_PATHS = [
        r"C:\Program Files\X-Plane 12",
        r"C:\Program Files\X-Plane 11",
        r"C:\Program Files (x86)\X-Plane 12",
        r"C:\Program Files (x86)\X-Plane 11",
        r"C:\X-Plane 12",
        r"C:\X-Plane 11",
        r"D:\X-Plane 12",
        r"D:\X-Plane 11",
        r"C:\Program Files (x86)\Steam\steamapps\common\X-Plane 12",
        r"C:\Program Files (x86)\Steam\steamapps\common\X-Plane 11",
    ]

    def __init__(self):
        """Initialize the X-Plane detector."""
        self._detected_path: Optional[Path] = None
        self._version: Optional[str] = None

    def detect(self, custom_path: Optional[str] = None) -> Tuple[Path, str]:
        """Detect X-Plane installation.

        Args:
            custom_path: Optional custom path to check first

        Returns:
            Tuple of (installation_path, version)

        Raises:
            XPlaneNotFoundError: If X-Plane cannot be found
        """
        # Check custom path first if provided
        if custom_path:
            if self._validate_xplane_path(custom_path):
                self._detected_path = Path(custom_path)
                self._version = self._detect_version(self._detected_path)
                return self._detected_path, self._version

        # Try to find in registry
        registry_path = self._check_registry()
        if registry_path and self._validate_xplane_path(registry_path):
            self._detected_path = Path(registry_path)
            self._version = self._detect_version(self._detected_path)
            return self._detected_path, self._version

        # Check common installation paths
        for path in self.COMMON_PATHS:
            if self._validate_xplane_path(path):
                self._detected_path = Path(path)
                self._version = self._detect_version(self._detected_path)
                return self._detected_path, self._version

        raise XPlaneNotFoundError(
            "X-Plane installation not found. Please specify the installation path manually."
        )

    def _check_registry(self) -> Optional[str]:
        """Check Windows registry for X-Plane installation path.

        Returns:
            Installation path if found, None otherwise
        """
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\X-Plane 12"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\X-Plane 11"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\X-Plane 12"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\X-Plane 11"),
        ]

        for hkey, subkey in registry_keys:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    path, _ = winreg.QueryValueEx(key, "InstallPath")
                    return path
            except (FileNotFoundError, OSError):
                continue

        return None

    def _validate_xplane_path(self, path: str) -> bool:
        """Validate if a path contains a valid X-Plane installation.

        Args:
            path: Path to check

        Returns:
            True if valid X-Plane installation, False otherwise
        """
        if not path or not os.path.exists(path):
            return False

        path_obj = Path(path)

        # Check for X-Plane executable
        exe_exists = (path_obj / "X-Plane.exe").exists() or (path_obj / "X-Plane.app").exists()
        if not exe_exists:
            return False

        # Check for Custom Scenery folder
        custom_scenery = path_obj / "Custom Scenery"
        if not custom_scenery.exists() or not custom_scenery.is_dir():
            return False

        return True

    def _detect_version(self, path: Path) -> str:
        """Detect X-Plane version from installation path.

        Args:
            path: X-Plane installation path

        Returns:
            Version string (e.g., "12", "11")
        """
        # Try to detect from folder name
        folder_name = path.name
        if "12" in folder_name:
            return "12"
        elif "11" in folder_name:
            return "11"

        # Try to read from version file
        version_file = path / "version.txt"
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    content = f.read().strip()
                    if "12" in content:
                        return "12"
                    elif "11" in content:
                        return "11"
            except Exception:
                pass

        # Default to unknown
        return "Unknown"

    def get_custom_scenery_path(self) -> Path:
        """Get the Custom Scenery folder path.

        Returns:
            Path to Custom Scenery folder

        Raises:
            XPlaneNotFoundError: If X-Plane not detected yet
        """
        if not self._detected_path:
            raise XPlaneNotFoundError("X-Plane installation not detected. Call detect() first.")

        return self._detected_path / "Custom Scenery"

    def get_scenery_packs_ini_path(self) -> Path:
        """Get the path to scenery_packs.ini file.

        Returns:
            Path to scenery_packs.ini

        Raises:
            XPlaneNotFoundError: If X-Plane not detected yet
        """
        return self.get_custom_scenery_path() / "scenery_packs.ini"

    @property
    def installation_path(self) -> Optional[Path]:
        """Get the detected X-Plane installation path."""
        return self._detected_path

    @property
    def version(self) -> Optional[str]:
        """Get the detected X-Plane version."""
        return self._version

    @staticmethod
    def list_available_installations() -> List[Tuple[Path, str]]:
        """List all available X-Plane installations found on the system.

        Returns:
            List of tuples (path, version) for each installation found
        """
        installations = []
        detector = XPlaneDetector()

        for path_str in detector.COMMON_PATHS:
            if detector._validate_xplane_path(path_str):
                path = Path(path_str)
                version = detector._detect_version(path)
                installations.append((path, version))

        # Also check registry
        registry_path = detector._check_registry()
        if registry_path and detector._validate_xplane_path(registry_path):
            path = Path(registry_path)
            version = detector._detect_version(path)
            # Avoid duplicates
            if not any(inst[0] == path for inst in installations):
                installations.append((path, version))

        return installations
