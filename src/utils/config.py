"""Configuration management for user preferences."""

import json
from pathlib import Path
from typing import Optional


class Config:
    """Manages application configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Optional path to config file (defaults to user's home directory)
        """
        if config_path:
            self.config_path = config_path
        else:
            # Default to .xplane_scenery_tool folder in user's home
            config_dir = Path.home() / ".xplane_scenery_tool"
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / "config.json"

        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            return self._get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                defaults = self._get_default_config()
                defaults.update(config)
                return defaults
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            'xplane_path': None,  # Manual X-Plane installation path
            'download_path': str(Path.home() / "Downloads" / "XPlaneSceneries"),  # Download folder
            'auto_extract': True,  # Auto-extract ZIPs when X-Plane not detected
            'theme': 'dark',  # UI theme (dark/light)
            'max_concurrent_downloads': 1,  # Maximum concurrent downloads
        }

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Failed to save config: {e}")

    def get(self, key: str, default=None):
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        self.save_config()

    def get_xplane_path(self) -> Optional[str]:
        """Get the configured X-Plane path.

        Returns:
            X-Plane path or None
        """
        return self.config.get('xplane_path')

    def set_xplane_path(self, path: Optional[str]):
        """Set the X-Plane installation path.

        Args:
            path: X-Plane installation path
        """
        self.set('xplane_path', path)

    def get_download_path(self) -> str:
        """Get the download folder path.

        Returns:
            Download folder path
        """
        return self.config.get('download_path', str(Path.home() / "Downloads" / "XPlaneSceneries"))

    def set_download_path(self, path: str):
        """Set the download folder path.

        Args:
            path: Download folder path
        """
        self.set('download_path', path)

    def get_auto_extract(self) -> bool:
        """Get auto-extract setting.

        Returns:
            True if auto-extract enabled
        """
        return self.config.get('auto_extract', True)

    def set_auto_extract(self, enabled: bool):
        """Set auto-extract setting.

        Args:
            enabled: True to enable auto-extract
        """
        self.set('auto_extract', enabled)
