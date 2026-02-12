"""Settings panel for user preferences."""

import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from typing import Callable

try:
    from ..utils.config import Config
except ImportError:
    from utils.config import Config


class SettingsPanel(ctk.CTkScrollableFrame):
    """Panel for application settings."""

    def __init__(self, parent, config: Config, on_save: Callable[[], None]):
        """Initialize the settings panel.

        Args:
            parent: Parent widget
            config: Configuration object
            on_save: Callback when settings are saved
        """
        super().__init__(parent)

        self.config = config
        self.on_save = on_save

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Header
        header = ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        header.grid(row=row, column=0, pady=(0, 20), sticky="w", padx=20)
        row += 1

        # X-Plane Path Section
        xplane_frame = ctk.CTkFrame(self)
        xplane_frame.grid(row=row, column=0, pady=10, sticky="ew", padx=20)
        xplane_frame.grid_columnconfigure(1, weight=1)
        row += 1

        xplane_label = ctk.CTkLabel(
            xplane_frame,
            text="X-Plane Installation Path",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        xplane_label.grid(row=0, column=0, columnspan=3, pady=(15, 5), padx=15, sticky="w")

        xplane_desc = ctk.CTkLabel(
            xplane_frame,
            text="Set this if X-Plane wasn't automatically detected",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray70"),
            anchor="w"
        )
        xplane_desc.grid(row=1, column=0, columnspan=3, pady=(0, 10), padx=15, sticky="w")

        self.xplane_path_entry = ctk.CTkEntry(
            xplane_frame,
            placeholder_text="C:\\Program Files\\X-Plane 12",
            height=40
        )
        self.xplane_path_entry.grid(row=2, column=0, columnspan=2, pady=(0, 15), padx=15, sticky="ew")

        current_path = self.config.get_xplane_path()
        if current_path:
            self.xplane_path_entry.insert(0, current_path)

        browse_xplane_btn = ctk.CTkButton(
            xplane_frame,
            text="Browse...",
            command=self._browse_xplane_path,
            width=100,
            height=40
        )
        browse_xplane_btn.grid(row=2, column=2, pady=(0, 15), padx=(5, 15))

        # Download Path Section
        download_frame = ctk.CTkFrame(self)
        download_frame.grid(row=row, column=0, pady=10, sticky="ew", padx=20)
        download_frame.grid_columnconfigure(1, weight=1)
        row += 1

        download_label = ctk.CTkLabel(
            download_frame,
            text="Download Folder",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        download_label.grid(row=0, column=0, columnspan=3, pady=(15, 5), padx=15, sticky="w")

        download_desc = ctk.CTkLabel(
            download_frame,
            text="Where sceneries are saved when X-Plane is not detected",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray70"),
            anchor="w"
        )
        download_desc.grid(row=1, column=0, columnspan=3, pady=(0, 10), padx=15, sticky="w")

        self.download_path_entry = ctk.CTkEntry(
            download_frame,
            placeholder_text=str(Path.home() / "Downloads" / "XPlaneSceneries"),
            height=40
        )
        self.download_path_entry.grid(row=2, column=0, columnspan=2, pady=(0, 15), padx=15, sticky="ew")
        self.download_path_entry.insert(0, self.config.get_download_path())

        browse_download_btn = ctk.CTkButton(
            download_frame,
            text="Browse...",
            command=self._browse_download_path,
            width=100,
            height=40
        )
        browse_download_btn.grid(row=2, column=2, pady=(0, 15), padx=(5, 15))

        # Auto-Extract Section
        extract_frame = ctk.CTkFrame(self)
        extract_frame.grid(row=row, column=0, pady=10, sticky="ew", padx=20)
        extract_frame.grid_columnconfigure(0, weight=1)
        row += 1

        extract_label = ctk.CTkLabel(
            extract_frame,
            text="Automatic Extraction",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        extract_label.grid(row=0, column=0, pady=(15, 5), padx=15, sticky="w")

        extract_desc = ctk.CTkLabel(
            extract_frame,
            text="Automatically extract ZIP files to folders (X-Plane needs extracted sceneries)",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray70"),
            anchor="w"
        )
        extract_desc.grid(row=1, column=0, pady=(0, 10), padx=15, sticky="w")

        self.auto_extract_switch = ctk.CTkSwitch(
            extract_frame,
            text="Auto-extract downloaded sceneries",
            font=ctk.CTkFont(size=13)
        )
        self.auto_extract_switch.grid(row=2, column=0, pady=(0, 15), padx=15, sticky="w")

        if self.config.get_auto_extract():
            self.auto_extract_switch.select()

        # Save Button
        save_button = ctk.CTkButton(
            self,
            text="Save Settings",
            command=self._save_settings,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        save_button.grid(row=row, column=0, pady=20, padx=20, sticky="ew")
        row += 1

        # Status message
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.grid(row=row, column=0, pady=(0, 20), padx=20, sticky="w")

    def _browse_xplane_path(self):
        """Browse for X-Plane installation directory."""
        path = filedialog.askdirectory(
            title="Select X-Plane Installation Folder",
            initialdir=str(Path.home())
        )
        if path:
            self.xplane_path_entry.delete(0, "end")
            self.xplane_path_entry.insert(0, path)

    def _browse_download_path(self):
        """Browse for download directory."""
        path = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=self.config.get_download_path()
        )
        if path:
            self.download_path_entry.delete(0, "end")
            self.download_path_entry.insert(0, path)

    def _save_settings(self):
        """Save settings to config."""
        # Get values
        xplane_path = self.xplane_path_entry.get().strip()
        download_path = self.download_path_entry.get().strip()
        auto_extract = self.auto_extract_switch.get()

        # Validate X-Plane path if provided
        if xplane_path:
            xplane_path_obj = Path(xplane_path)
            if not xplane_path_obj.exists():
                self.status_label.configure(
                    text="❌ X-Plane path does not exist",
                    text_color=("#C62828", "#EF5350")
                )
                return

            # Check for X-Plane.exe or Custom Scenery folder
            if not (xplane_path_obj / "X-Plane.exe").exists() and \
               not (xplane_path_obj / "Custom Scenery").exists():
                self.status_label.configure(
                    text="⚠️ Warning: This doesn't look like an X-Plane installation",
                    text_color=("#E65100", "#FF9800")
                )
                # Allow saving anyway, just warn

        # Validate download path
        if download_path:
            download_path_obj = Path(download_path)
            try:
                download_path_obj.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.status_label.configure(
                    text=f"❌ Cannot create download folder: {str(e)}",
                    text_color=("#C62828", "#EF5350")
                )
                return

        # Save to config
        self.config.set_xplane_path(xplane_path if xplane_path else None)
        self.config.set_download_path(download_path)
        self.config.set_auto_extract(auto_extract)

        self.status_label.configure(
            text="✅ Settings saved successfully!",
            text_color=("#2E7D32", "#66BB6A")
        )

        # Trigger callback
        if self.on_save:
            self.on_save()
