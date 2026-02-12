"""Scenery installation and management."""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from .xplane_detector import XPlaneDetector, XPlaneNotFoundError

try:
    from ..models.scenery import Scenery, InstalledScenery
except ImportError:
    from models.scenery import Scenery, InstalledScenery


class SceneryManagerError(Exception):
    """Custom exception for scenery manager errors."""
    pass


class SceneryManager:
    """Manages scenery installation, tracking, and removal."""

    def __init__(self, xplane_path: Optional[Path] = None, data_dir: Optional[Path] = None):
        """Initialize the scenery manager.

        Args:
            xplane_path: Optional X-Plane installation path (auto-detect if not provided)
            data_dir: Optional data directory for tracking installed sceneries
        """
        # Detect or use provided X-Plane installation
        if xplane_path:
            self.detector = XPlaneDetector()
            if not self.detector._validate_xplane_path(str(xplane_path)):
                raise XPlaneNotFoundError(f"Invalid X-Plane installation at: {xplane_path}")
            self.detector._detected_path = xplane_path
            self.detector._version = self.detector._detect_version(xplane_path)
        else:
            self.detector = XPlaneDetector()
            try:
                self.detector.detect()
            except XPlaneNotFoundError:
                # Allow initialization without X-Plane for testing
                pass

        # Set up data directory for tracking
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to project root / data
            self.data_dir = Path(__file__).parent.parent.parent / "data"

        self.data_dir.mkdir(exist_ok=True)
        self.installed_db_path = self.data_dir / "installed_sceneries.json"

        # Load installed sceneries database
        self.installed_sceneries: Dict[int, InstalledScenery] = self._load_installed_db()

    def _load_installed_db(self) -> Dict[int, InstalledScenery]:
        """Load the installed sceneries database from JSON.

        Returns:
            Dictionary mapping scenery_id to InstalledScenery
        """
        if not self.installed_db_path.exists():
            return {}

        try:
            with open(self.installed_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(sid): InstalledScenery(**info)
                    for sid, info in data.items()
                }
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Warning: Failed to load installed sceneries database: {e}")
            return {}

    def _save_installed_db(self):
        """Save the installed sceneries database to JSON."""
        data = {
            str(sid): {
                'scenery_id': inst.scenery_id,
                'airport_icao': inst.airport_icao,
                'installed_date': inst.installed_date,
                'install_path': inst.install_path,
                'version': inst.version
            }
            for sid, inst in self.installed_sceneries.items()
        }

        with open(self.installed_db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def install_scenery(self, scenery: Scenery, zip_data: bytes) -> InstalledScenery:
        """Install a scenery pack from ZIP data.

        Args:
            scenery: Scenery metadata
            zip_data: Binary ZIP file data

        Returns:
            InstalledScenery object with installation details

        Raises:
            SceneryManagerError: If installation fails
        """
        if not self.detector.installation_path:
            raise SceneryManagerError("X-Plane installation not detected")

        # Generate scenery folder name
        folder_name = f"{scenery.airport_icao}_{scenery.id}"
        install_path = self.detector.get_custom_scenery_path() / folder_name

        # Check if already installed
        if install_path.exists():
            raise SceneryManagerError(
                f"Scenery already exists at {install_path}. Uninstall first to reinstall."
            )

        try:
            # Extract ZIP to Custom Scenery folder
            self._extract_zip(zip_data, install_path)

            # Update scenery_packs.ini
            self._update_scenery_packs_ini(folder_name)

            # Create installed scenery record
            installed = InstalledScenery(
                scenery_id=scenery.id,
                airport_icao=scenery.airport_icao,
                installed_date=datetime.now().isoformat(),
                install_path=str(install_path),
                version=self.detector.version or "Unknown"
            )

            # Add to database
            self.installed_sceneries[scenery.id] = installed
            self._save_installed_db()

            return installed

        except Exception as e:
            # Clean up on failure
            if install_path.exists():
                shutil.rmtree(install_path, ignore_errors=True)
            raise SceneryManagerError(f"Failed to install scenery: {str(e)}")

    def _extract_zip(self, zip_data: bytes, destination: Path):
        """Extract ZIP data to destination folder.

        Args:
            zip_data: Binary ZIP file data
            destination: Destination folder path

        Raises:
            SceneryManagerError: If extraction fails
        """
        try:
            # Create temporary file for ZIP
            temp_zip = self.data_dir / "temp_scenery.zip"
            with open(temp_zip, 'wb') as f:
                f.write(zip_data)

            # Extract with security checks
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                # Validate no path traversal attacks
                for member in zip_ref.namelist():
                    if member.startswith('/') or '..' in member:
                        raise SceneryManagerError(
                            f"Invalid ZIP file: contains unsafe path '{member}'"
                        )

                # Extract all files
                zip_ref.extractall(destination)

            # Clean up temporary file
            temp_zip.unlink()

        except zipfile.BadZipFile:
            raise SceneryManagerError("Invalid or corrupted ZIP file")
        except Exception as e:
            raise SceneryManagerError(f"Failed to extract ZIP: {str(e)}")

    def _update_scenery_packs_ini(self, folder_name: str):
        """Update scenery_packs.ini to include new scenery.

        Args:
            folder_name: Name of the scenery folder

        Raises:
            SceneryManagerError: If update fails
        """
        ini_path = self.detector.get_scenery_packs_ini_path()

        # Create backup
        if ini_path.exists():
            backup_path = ini_path.with_suffix('.ini.backup')
            shutil.copy2(ini_path, backup_path)

        try:
            # Read existing content
            lines = []
            if ini_path.exists():
                with open(ini_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

            # Check if already in file
            entry = f"SCENERY_PACK Custom Scenery/{folder_name}/\n"
            if entry in lines:
                return  # Already present

            # Add new entry at the top (after header comments)
            insert_index = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#'):
                    insert_index = i
                    break

            lines.insert(insert_index, entry)

            # Write updated content
            with open(ini_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

        except Exception as e:
            # Restore backup on failure
            if ini_path.exists() and backup_path.exists():
                shutil.copy2(backup_path, ini_path)
            raise SceneryManagerError(f"Failed to update scenery_packs.ini: {str(e)}")

    def uninstall_scenery(self, scenery_id: int):
        """Uninstall a scenery pack.

        Args:
            scenery_id: ID of the scenery to uninstall

        Raises:
            SceneryManagerError: If uninstallation fails
        """
        if scenery_id not in self.installed_sceneries:
            raise SceneryManagerError(f"Scenery {scenery_id} is not installed")

        installed = self.installed_sceneries[scenery_id]
        install_path = Path(installed.install_path)

        try:
            # Remove scenery folder
            if install_path.exists():
                shutil.rmtree(install_path)

            # Remove from scenery_packs.ini
            folder_name = install_path.name
            self._remove_from_scenery_packs_ini(folder_name)

            # Remove from database
            del self.installed_sceneries[scenery_id]
            self._save_installed_db()

        except Exception as e:
            raise SceneryManagerError(f"Failed to uninstall scenery: {str(e)}")

    def _remove_from_scenery_packs_ini(self, folder_name: str):
        """Remove scenery entry from scenery_packs.ini.

        Args:
            folder_name: Name of the scenery folder
        """
        ini_path = self.detector.get_scenery_packs_ini_path()

        if not ini_path.exists():
            return

        # Create backup
        backup_path = ini_path.with_suffix('.ini.backup')
        shutil.copy2(ini_path, backup_path)

        try:
            with open(ini_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Remove matching line
            entry = f"SCENERY_PACK Custom Scenery/{folder_name}/\n"
            lines = [line for line in lines if line != entry]

            with open(ini_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

        except Exception as e:
            # Restore backup on failure
            if backup_path.exists():
                shutil.copy2(backup_path, ini_path)
            raise SceneryManagerError(f"Failed to update scenery_packs.ini: {str(e)}")

    def is_installed(self, scenery_id: int) -> bool:
        """Check if a scenery is installed.

        Args:
            scenery_id: ID of the scenery

        Returns:
            True if installed, False otherwise
        """
        return scenery_id in self.installed_sceneries

    def get_installed_scenery(self, scenery_id: int) -> Optional[InstalledScenery]:
        """Get information about an installed scenery.

        Args:
            scenery_id: ID of the scenery

        Returns:
            InstalledScenery object or None if not installed
        """
        return self.installed_sceneries.get(scenery_id)

    def list_installed_sceneries(self) -> List[InstalledScenery]:
        """Get a list of all installed sceneries.

        Returns:
            List of InstalledScenery objects
        """
        return list(self.installed_sceneries.values())

    def get_xplane_info(self) -> Dict[str, str]:
        """Get information about the detected X-Plane installation.

        Returns:
            Dictionary with installation info
        """
        if not self.detector.installation_path:
            return {
                'status': 'not_detected',
                'message': 'X-Plane installation not found'
            }

        return {
            'status': 'detected',
            'path': str(self.detector.installation_path),
            'version': self.detector.version or 'Unknown',
            'custom_scenery_path': str(self.detector.get_custom_scenery_path())
        }
