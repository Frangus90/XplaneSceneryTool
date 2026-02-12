"""Details panel for displaying full airport and scenery information."""

import customtkinter as ctk
import webbrowser
from typing import Callable, List
from datetime import datetime

try:
    from ..models.airport import Airport
    from ..models.scenery import Scenery
except ImportError:
    from models.airport import Airport
    from models.scenery import Scenery


class DetailsPanel(ctk.CTkScrollableFrame):
    """Panel for displaying detailed airport and scenery version history."""

    def __init__(
        self,
        parent,
        on_download: Callable[[Scenery], None],
        on_back: Callable[[], None]
    ):
        """Initialize the details panel.

        Args:
            parent: Parent widget
            on_download: Callback when downloading a scenery
            on_back: Callback when going back to results
        """
        super().__init__(parent)

        self.on_download = on_download
        self.on_back = on_back

        self.airport: Airport = None
        self.sceneries: List[Scenery] = []

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

    def display_details(self, airport: Airport, sceneries: List[Scenery]):
        """Display detailed airport and scenery information.

        Args:
            airport: Airport data
            sceneries: List of all scenery packs for the airport
        """
        self.airport = airport
        self.sceneries = sceneries

        # Clear previous content
        for widget in self.winfo_children():
            widget.destroy()

        row = 0

        # Back button
        back_button = ctk.CTkButton(
            self,
            text="← Back to Results",
            command=self.on_back,
            width=150,
            height=32,
            fg_color="transparent",
            border_width=2
        )
        back_button.grid(row=row, column=0, pady=(0, 20), sticky="w")
        row += 1

        # Airport header
        header_frame = ctk.CTkFrame(self, fg_color=("#E3F2FD", "#0D47A1"))
        header_frame.grid(row=row, column=0, pady=(0, 20), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        row += 1

        # Airport name
        name_label = ctk.CTkLabel(
            header_frame,
            text=f"{airport.name} ({airport.icao})",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w"
        )
        name_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        # Coordinates
        coords_label = ctk.CTkLabel(
            header_frame,
            text=f"📍 Coordinates: {airport.latitude:.6f}, {airport.longitude:.6f}",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        coords_label.grid(row=1, column=0, padx=20, pady=2, sticky="w")

        # Last updated
        if airport.last_updated:
            try:
                date_obj = datetime.fromisoformat(airport.last_updated.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%B %d, %Y at %H:%M UTC")
                update_text = f"🕒 Last Updated: {formatted_date}"
            except:
                update_text = f"🕒 Last Updated: {airport.last_updated}"

            update_label = ctk.CTkLabel(
                header_frame,
                text=update_text,
                font=ctk.CTkFont(size=13),
                anchor="w"
            )
            update_label.grid(row=2, column=0, padx=20, pady=(2, 20), sticky="w")

        # Total sceneries count
        count_label = ctk.CTkLabel(
            header_frame,
            text=f"📦 {len(sceneries)} Scenery Version(s) Available",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        count_label.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="w")

        # Gateway website link
        gateway_url = f"https://gateway.x-plane.com/airports/{airport.icao}/show"
        gateway_button = ctk.CTkButton(
            header_frame,
            text="🌐 View on X-Plane Gateway Website",
            command=lambda: webbrowser.open(gateway_url),
            fg_color="transparent",
            hover_color=("#1565C0", "#42A5F5"),
            border_width=2,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        gateway_button.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="w")

        # Scenery version history section
        history_header = ctk.CTkLabel(
            self,
            text="Scenery Version History",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        )
        history_header.grid(row=row, column=0, pady=(10, 15), sticky="w")
        row += 1

        # Display sceneries (chronological, newest first)
        sorted_sceneries = sorted(
            sceneries,
            key=lambda s: s.date_uploaded or "",
            reverse=True
        )

        for scenery in sorted_sceneries:
            is_recommended = (scenery.id == airport.recommended_scenery_id)
            self._create_version_card(scenery, row, is_recommended)
            row += 1

    def _create_version_card(self, scenery: Scenery, row: int, is_recommended: bool):
        """Create a detailed card for a scenery version.

        Args:
            scenery: Scenery data
            row: Grid row position
            is_recommended: Whether this is the recommended version
        """
        # Card frame with status color
        status_colors = {
            "Approved": ("#E8F5E9", "#1B5E20"),
            "Declined": ("#FFEBEE", "#B71C1C"),
            "Pending": ("#FFF3E0", "#E65100"),
        }
        card_color = status_colors.get(scenery.status, ("gray90", "gray20"))

        card = ctk.CTkFrame(self, fg_color=card_color)
        card.grid(row=row, column=0, pady=8, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        card_row = 0

        # Badges row
        badges_frame = ctk.CTkFrame(card, fg_color="transparent")
        badges_frame.grid(row=card_row, column=0, columnspan=2, padx=15, pady=(12, 8), sticky="w")
        card_row += 1

        badge_col = 0

        # Recommended badge
        if is_recommended:
            rec_badge = ctk.CTkLabel(
                badges_frame,
                text="⭐ RECOMMENDED",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=("#4CAF50", "#2E7D32"),
                corner_radius=4,
                padx=8,
                pady=2
            )
            rec_badge.grid(row=0, column=badge_col, padx=(0, 5))
            badge_col += 1

        # Status badge
        status_badge_colors = {
            "Approved": ("#4CAF50", "#2E7D32"),
            "Declined": ("#F44336", "#C62828"),
            "Pending": ("#FF9800", "#E65100"),
        }
        badge_color = status_badge_colors.get(scenery.status, ("gray", "gray"))

        status_badge = ctk.CTkLabel(
            badges_frame,
            text=scenery.status.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=badge_color,
            corner_radius=4,
            padx=8,
            pady=2
        )
        status_badge.grid(row=0, column=badge_col, padx=(0, 5))
        badge_col += 1

        # 3D badge
        if scenery.type == "3D":
            type_badge = ctk.CTkLabel(
                badges_frame,
                text="🎨 3D",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=("#2196F3", "#1565C0"),
                corner_radius=4,
                padx=8,
                pady=2
            )
            type_badge.grid(row=0, column=badge_col, padx=(0, 5))
            badge_col += 1

        # Editor's Choice badge
        if scenery.is_editors_choice:
            choice_badge = ctk.CTkLabel(
                badges_frame,
                text="🏆 EDITOR'S CHOICE",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=("#9C27B0", "#6A1B9A"),
                corner_radius=4,
                padx=8,
                pady=2
            )
            choice_badge.grid(row=0, column=badge_col)

        # Version ID and artist
        title_text = f"Version {scenery.id} by {scenery.artist_name}"
        title_label = ctk.CTkLabel(
            card,
            text=title_text,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=card_row, column=0, padx=15, pady=(0, 5), sticky="w")
        card_row += 1

        # Dates
        dates_text = []
        if scenery.date_uploaded:
            try:
                date_obj = datetime.fromisoformat(scenery.date_uploaded.replace('Z', '+00:00'))
                formatted = date_obj.strftime("%b %d, %Y")
                dates_text.append(f"📅 Uploaded: {formatted}")
            except:
                dates_text.append(f"📅 Uploaded: {scenery.date_uploaded}")

        if scenery.date_approved:
            try:
                date_obj = datetime.fromisoformat(scenery.date_approved.replace('Z', '+00:00'))
                formatted = date_obj.strftime("%b %d, %Y")
                dates_text.append(f"✅ Approved: {formatted}")
            except:
                dates_text.append(f"✅ Approved: {scenery.date_approved}")

        if dates_text:
            dates_label = ctk.CTkLabel(
                card,
                text=" • ".join(dates_text),
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray70"),
                anchor="w"
            )
            dates_label.grid(row=card_row, column=0, padx=15, pady=(0, 5), sticky="w")
            card_row += 1

        # Technical info
        tech_info = []
        if scenery.wed_version:
            tech_info.append(f"WED {scenery.wed_version}")
        if scenery.xplane_version:
            tech_info.append(f"X-Plane {scenery.xplane_version}")

        if tech_info:
            tech_label = ctk.CTkLabel(
                card,
                text=" • ".join(tech_info),
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray70"),
                anchor="w"
            )
            tech_label.grid(row=card_row, column=0, padx=15, pady=(0, 8), sticky="w")
            card_row += 1

        # Features
        if scenery.features:
            features_text = "✨ Features: " + ", ".join(scenery.features)
            features_label = ctk.CTkLabel(
                card,
                text=features_text,
                font=ctk.CTkFont(size=11),
                anchor="w",
                wraplength=700
            )
            features_label.grid(row=card_row, column=0, padx=15, pady=(0, 8), sticky="w")
            card_row += 1

        # Artist comments (collapsible)
        if scenery.artist_comments:
            self._add_collapsible_section(
                card,
                card_row,
                "💬 Artist Comments",
                scenery.artist_comments
            )
            card_row += 1

        # Moderator comments (collapsible)
        if scenery.moderator_comments:
            self._add_collapsible_section(
                card,
                card_row,
                "👤 Moderator Comments",
                scenery.moderator_comments
            )
            card_row += 1

        # Download button
        download_button = ctk.CTkButton(
            card,
            text="Download This Version",
            command=lambda s=scenery: self.on_download(s),
            width=180,
            height=32
        )
        download_button.grid(row=0, column=1, rowspan=card_row, padx=15, pady=15, sticky="ne")

    def _add_collapsible_section(self, parent, row: int, title: str, content: str):
        """Add a collapsible text section.

        Args:
            parent: Parent widget
            row: Grid row position
            title: Section title
            content: Section content text
        """
        # Container for section
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.grid(row=row, column=0, padx=15, pady=(0, 8), sticky="ew")
        section_frame.grid_columnconfigure(0, weight=1)

        # State variable
        is_expanded = ctk.BooleanVar(value=False)

        # Toggle button
        toggle_button = ctk.CTkButton(
            section_frame,
            text=f"▶ {title}",
            command=lambda: self._toggle_section(toggle_button, text_box, is_expanded, title),
            fg_color="transparent",
            text_color=("#1976D2", "#64B5F6"),
            hover=False,
            anchor="w",
            height=24
        )
        toggle_button.grid(row=0, column=0, sticky="w")

        # Collapsible text box (hidden by default)
        text_box = ctk.CTkTextbox(
            section_frame,
            height=80,
            wrap="word",
            font=ctk.CTkFont(size=11)
        )
        text_box.insert("1.0", content)
        text_box.configure(state="disabled")

    def _toggle_section(self, button, textbox, state_var, title: str):
        """Toggle a collapsible section.

        Args:
            button: Toggle button
            textbox: Text box to show/hide
            state_var: State variable
            title: Section title
        """
        state_var.set(not state_var.get())

        if state_var.get():
            button.configure(text=f"▼ {title}")
            textbox.grid(row=1, column=0, pady=(5, 0), sticky="ew")
        else:
            button.configure(text=f"▶ {title}")
            textbox.grid_forget()
