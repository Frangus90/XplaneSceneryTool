"""Main application window for X-Plane Scenery Tool."""

import customtkinter as ctk
from typing import Optional
from pathlib import Path


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Window configuration
        self.title("X-Plane Scenery Tool")
        self.geometry("1000x700")
        self.minsize(800, 600)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configure grid layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Navigation tabs
        self.nav_frame = ctk.CTkFrame(self, height=50, fg_color=("#DBDBDB", "#2B2B2B"))
        self.nav_frame.grid(row=0, column=0, sticky="ew")
        self.nav_frame.grid_columnconfigure(0, weight=1)
        self.nav_frame.grid_columnconfigure(1, weight=1)
        self.nav_frame.grid_columnconfigure(2, weight=1)

        self.search_tab_button = ctk.CTkButton(
            self.nav_frame,
            text="🔍 Search",
            command=lambda: self.on_tab_change("search"),
            height=40,
            fg_color="transparent",
            text_color=("#1f6aa5", "#4da6ff"),
            hover_color=("#E3F2FD", "#1565C0"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.search_tab_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.downloads_tab_button = ctk.CTkButton(
            self.nav_frame,
            text="📥 Downloads",
            command=lambda: self.on_tab_change("downloads"),
            height=40,
            fg_color="transparent",
            hover_color=("#E3F2FD", "#1565C0"),
            font=ctk.CTkFont(size=14)
        )
        self.downloads_tab_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.settings_tab_button = ctk.CTkButton(
            self.nav_frame,
            text="⚙️ Settings",
            command=lambda: self.on_tab_change("settings"),
            height=40,
            fg_color="transparent",
            hover_color=("#E3F2FD", "#1565C0"),
            font=ctk.CTkFont(size=14)
        )
        self.settings_tab_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Current view state
        self.current_panel = None
        self.current_tab = "search"
        self.tab_change_callback = None

        # Create main container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Status bar at bottom
        self.status_bar = ctk.CTkLabel(
            self,
            text="Ready",
            anchor="w",
            fg_color=("#E0E0E0", "#2B2B2B"),
            corner_radius=0,
            height=30,
            padx=10
        )
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def show_panel(self, panel):
        """Show a panel in the main container.

        Args:
            panel: Panel widget to display
        """
        # Hide current panel
        if self.current_panel:
            self.current_panel.grid_forget()

        # Show new panel
        panel.grid(row=0, column=0, sticky="nsew", in_=self.container)
        self.current_panel = panel

    def set_status(self, message: str, status_type: str = "info"):
        """Update the status bar message.

        Args:
            message: Status message to display
            status_type: Type of status ("info", "success", "error", "warning")
        """
        # Color coding for different status types
        colors = {
            "info": ("#E0E0E0", "#2B2B2B"),
            "success": ("#C8E6C9", "#2E7D32"),
            "error": ("#FFCDD2", "#C62828"),
            "warning": ("#FFE082", "#F57C00")
        }

        fg_color = colors.get(status_type, colors["info"])
        self.status_bar.configure(text=message, fg_color=fg_color)

    def clear_status(self):
        """Clear the status bar."""
        self.set_status("Ready")

    def set_tab_change_callback(self, callback):
        """Set the callback for tab changes.

        Args:
            callback: Function to call when tab changes (receives tab name)
        """
        self.tab_change_callback = callback

    def on_tab_change(self, tab: str):
        """Handle tab change.

        Args:
            tab: Tab name ("search", "downloads", or "settings")
        """
        self.current_tab = tab

        # Update button styles - reset all first
        self.search_tab_button.configure(
            text_color=("gray50", "gray70"),
            font=ctk.CTkFont(size=14)
        )
        self.downloads_tab_button.configure(
            text_color=("gray50", "gray70"),
            font=ctk.CTkFont(size=14)
        )
        self.settings_tab_button.configure(
            text_color=("gray50", "gray70"),
            font=ctk.CTkFont(size=14)
        )

        # Highlight active tab
        if tab == "search":
            self.search_tab_button.configure(
                text_color=("#1f6aa5", "#4da6ff"),
                font=ctk.CTkFont(size=14, weight="bold")
            )
        elif tab == "downloads":
            self.downloads_tab_button.configure(
                text_color=("#1f6aa5", "#4da6ff"),
                font=ctk.CTkFont(size=14, weight="bold")
            )
        elif tab == "settings":
            self.settings_tab_button.configure(
                text_color=("#1f6aa5", "#4da6ff"),
                font=ctk.CTkFont(size=14, weight="bold")
            )

        # Trigger callback
        if self.tab_change_callback:
            self.tab_change_callback(tab)

    def update_downloads_badge(self, count: int):
        """Update the downloads tab with a badge count.

        Args:
            count: Number of active downloads
        """
        if count > 0:
            self.downloads_tab_button.configure(text=f"📥 Downloads ({count})")
        else:
            self.downloads_tab_button.configure(text="📥 Downloads")
