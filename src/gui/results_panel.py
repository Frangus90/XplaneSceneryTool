"""Results panel for displaying airport search results."""

import customtkinter as ctk
from typing import Callable
from datetime import datetime

try:
    from ..models.airport import Airport
except ImportError:
    from models.airport import Airport


class ResultsPanel(ctk.CTkScrollableFrame):
    """Panel for displaying search results."""

    def __init__(
        self,
        parent,
        on_view_details: Callable[[Airport], None],
        on_back: Callable[[], None]
    ):
        """Initialize the results panel.

        Args:
            parent: Parent widget
            on_view_details: Callback when viewing airport details (airport)
            on_back: Callback when going back to search
        """
        super().__init__(parent)

        self.on_view_details = on_view_details
        self.on_back = on_back

        self.airport: Airport = None

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

    def display_results(self, airport: Airport):
        """Display search results.

        Args:
            airport: Airport data
        """
        self.airport = airport

        # Clear previous results
        for widget in self.winfo_children():
            widget.destroy()

        row = 0

        # Back button
        back_button = ctk.CTkButton(
            self,
            text="← Back to Search",
            command=self.on_back,
            width=150,
            height=32,
            fg_color="transparent",
            border_width=2
        )
        back_button.grid(row=row, column=0, pady=(0, 20), sticky="w")
        row += 1

        # Airport card
        airport_frame = ctk.CTkFrame(self, fg_color=("#E3F2FD", "#0D47A1"))
        airport_frame.grid(row=row, column=0, pady=(0, 20), sticky="ew")
        airport_frame.grid_columnconfigure(0, weight=1)
        row += 1

        # Airport name and ICAO
        name_label = ctk.CTkLabel(
            airport_frame,
            text=f"{airport.name} ({airport.icao})",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        name_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        # Location
        location_label = ctk.CTkLabel(
            airport_frame,
            text=f"📍 Coordinates: {airport.latitude:.6f}, {airport.longitude:.6f}",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        location_label.grid(row=1, column=0, padx=20, pady=2, sticky="w")

        # Last updated
        if airport.last_updated:
            try:
                date_obj = datetime.fromisoformat(airport.last_updated.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%B %d, %Y at %H:%M UTC")
                update_text = f"🕒 Last Updated: {formatted_date}"
            except:
                update_text = f"🕒 Last Updated: {airport.last_updated}"

            update_label = ctk.CTkLabel(
                airport_frame,
                text=update_text,
                font=ctk.CTkFont(size=13),
                anchor="w"
            )
            update_label.grid(row=2, column=0, padx=20, pady=(2, 5), sticky="w")

        # Scenery count
        count_label = ctk.CTkLabel(
            airport_frame,
            text=f"📦 {len(airport.scenery_ids)} Scenery Version(s) Available",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        count_label.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="w")

        # View Details button
        details_button = ctk.CTkButton(
            self,
            text="View Scenery Details & Version History →",
            command=self._view_details,
            height=50,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        details_button.grid(row=row, column=0, pady=20, sticky="ew")

    def _view_details(self):
        """View full airport details."""
        if self.airport:
            self.on_view_details(self.airport)
