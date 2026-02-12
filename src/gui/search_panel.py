"""Search panel for entering ICAO codes."""

import customtkinter as ctk
from typing import Callable, Optional


class SearchPanel(ctk.CTkFrame):
    """Panel for searching airports by ICAO code."""

    def __init__(self, parent, on_search: Callable[[str], None]):
        """Initialize the search panel.

        Args:
            parent: Parent widget
            on_search: Callback function when search is triggered (receives ICAO code)
        """
        super().__init__(parent)

        self.on_search = on_search

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            self,
            text="X-Plane Scenery Gateway Search",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, pady=(20, 10), sticky="w", padx=20)

        # Description
        description = ctk.CTkLabel(
            self,
            text="Search for airport sceneries by ICAO code (e.g., KJFK, EGLL, ESSA)",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        description.grid(row=1, column=0, pady=(0, 20), sticky="w", padx=20)

        # Search container
        search_container = ctk.CTkFrame(self, fg_color="transparent")
        search_container.grid(row=2, column=0, pady=10, sticky="ew", padx=20)
        search_container.grid_columnconfigure(0, weight=1)

        # ICAO input
        self.icao_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="Enter ICAO code (e.g., KJFK)",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.icao_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.icao_entry.bind("<Return>", lambda e: self._on_search_clicked())

        # Search button
        self.search_button = ctk.CTkButton(
            search_container,
            text="Search",
            command=self._on_search_clicked,
            height=40,
            width=120,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.search_button.grid(row=0, column=1)

        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        self.status_label.grid(row=3, column=0, pady=(5, 10), sticky="w", padx=20)

        # Loading indicator (hidden by default)
        self.loading_label = ctk.CTkLabel(
            self,
            text="🔍 Searching...",
            font=ctk.CTkFont(size=14),
            text_color=("#1f6aa5", "#1f6aa5")
        )

    def _on_search_clicked(self):
        """Handle search button click."""
        icao = self.icao_entry.get().strip().upper()

        # Validate ICAO
        if not icao:
            self.show_error("Please enter an ICAO code")
            return

        if len(icao) < 3 or len(icao) > 4:
            self.show_error("ICAO code must be 3-4 characters")
            return

        if not icao.isalpha():
            self.show_error("ICAO code must contain only letters")
            return

        # Clear status and trigger search
        self.clear_status()
        self.on_search(icao)

    def show_loading(self):
        """Show loading indicator."""
        self.search_button.configure(state="disabled")
        self.icao_entry.configure(state="disabled")
        self.loading_label.grid(row=4, column=0, pady=10, padx=20)

    def hide_loading(self):
        """Hide loading indicator."""
        self.search_button.configure(state="normal")
        self.icao_entry.configure(state="normal")
        self.loading_label.grid_forget()

    def show_error(self, message: str):
        """Show error message.

        Args:
            message: Error message to display
        """
        self.status_label.configure(text=f"❌ {message}", text_color=("#C62828", "#EF5350"))

    def show_success(self, message: str):
        """Show success message.

        Args:
            message: Success message to display
        """
        self.status_label.configure(text=f"✓ {message}", text_color=("#2E7D32", "#66BB6A"))

    def clear_status(self):
        """Clear status message."""
        self.status_label.configure(text="")

    def set_icao(self, icao: str):
        """Set the ICAO input value.

        Args:
            icao: ICAO code to set
        """
        self.icao_entry.delete(0, "end")
        self.icao_entry.insert(0, icao.upper())

    def get_icao(self) -> str:
        """Get the current ICAO input value.

        Returns:
            Current ICAO code
        """
        return self.icao_entry.get().strip().upper()
