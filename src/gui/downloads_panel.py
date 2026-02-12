"""Downloads panel for displaying download queue and progress."""

import customtkinter as ctk
from typing import Callable

try:
    from ..core.download_queue import DownloadTask, DownloadStatus
except ImportError:
    from core.download_queue import DownloadTask, DownloadStatus


class DownloadsPanel(ctk.CTkScrollableFrame):
    """Panel for displaying download queue and progress."""

    def __init__(self, parent, on_cancel: Callable[[int], None], on_clear: Callable[[], None]):
        """Initialize the downloads panel.

        Args:
            parent: Parent widget
            on_cancel: Callback when cancelling a download (receives scenery_id)
            on_clear: Callback when clearing completed downloads
        """
        super().__init__(parent)

        self.on_cancel = on_cancel
        self.on_clear = on_clear

        # Task widgets storage
        self.task_widgets: dict[int, dict] = {}  # scenery_id -> {widgets}

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)

        header_label = ctk.CTkLabel(
            self.header_frame,
            text="Downloads",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        )
        header_label.grid(row=0, column=0, sticky="w")

        # Clear completed button
        self.clear_button = ctk.CTkButton(
            self.header_frame,
            text="Clear Completed",
            command=on_clear,
            width=140,
            height=32,
            fg_color="transparent",
            border_width=2
        )
        self.clear_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Container for task cards
        self.tasks_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tasks_container.grid(row=1, column=0, sticky="ew")
        self.tasks_container.grid_columnconfigure(0, weight=1)

        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.tasks_container,
            text="No downloads in queue",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray70")
        )
        self.empty_label.grid(row=0, column=0, pady=40)

    def update_task(self, task: DownloadTask):
        """Update or create a task card.

        Args:
            task: Download task to display
        """
        scenery_id = task.scenery.id

        # Hide empty label
        self.empty_label.grid_forget()

        # Create new card if doesn't exist
        if scenery_id not in self.task_widgets:
            self._create_task_card(task)
        else:
            self._update_task_card(task)

    def remove_task(self, scenery_id: int):
        """Remove a task card.

        Args:
            scenery_id: Scenery ID to remove
        """
        if scenery_id in self.task_widgets:
            widgets = self.task_widgets[scenery_id]
            widgets['card'].destroy()
            del self.task_widgets[scenery_id]

        # Show empty label if no tasks
        if not self.task_widgets:
            self.empty_label.grid(row=0, column=0, pady=40)

    def clear_all_tasks(self):
        """Clear all task cards."""
        for scenery_id in list(self.task_widgets.keys()):
            self.remove_task(scenery_id)

    def _create_task_card(self, task: DownloadTask):
        """Create a new task card.

        Args:
            task: Download task
        """
        scenery_id = task.scenery.id
        row = len(self.task_widgets)

        # Card frame
        card = ctk.CTkFrame(self.tasks_container)
        card.grid(row=row, column=0, pady=5, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        # Status color
        status_colors = {
            DownloadStatus.QUEUED: ("gray90", "gray20"),
            DownloadStatus.DOWNLOADING: ("#E3F2FD", "#0D47A1"),
            DownloadStatus.EXTRACTING: ("#FFF3E0", "#E65100"),
            DownloadStatus.INSTALLING: ("#F3E5F5", "#6A1B9A"),
            DownloadStatus.COMPLETED: ("#E8F5E9", "#1B5E20"),
            DownloadStatus.FAILED: ("#FFEBEE", "#B71C1C"),
            DownloadStatus.CANCELLED: ("gray85", "gray25"),
        }
        card.configure(fg_color=status_colors.get(task.status, ("gray90", "gray20")))

        # Airport ICAO and scenery ID
        title_label = ctk.CTkLabel(
            card,
            text=f"{task.scenery.airport_icao} - Scenery #{task.scenery.id}",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, padx=15, pady=(12, 5), sticky="w")

        # Status and artist info
        info_text = f"by {task.scenery.artist_name}"
        info_label = ctk.CTkLabel(
            card,
            text=info_text,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray70"),
            anchor="w"
        )
        info_label.grid(row=1, column=0, padx=15, pady=(0, 8), sticky="w")

        # Progress bar
        progress_bar = ctk.CTkProgressBar(card, width=300, height=8)
        progress_bar.grid(row=2, column=0, padx=15, pady=(0, 5), sticky="ew")
        progress_bar.set(task.progress / 100.0)

        # Status label
        status_label = ctk.CTkLabel(
            card,
            text=self._get_status_text(task),
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        status_label.grid(row=3, column=0, padx=15, pady=(0, 12), sticky="w")

        # Action button (cancel or retry)
        action_button = None
        if task.status in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING,
                          DownloadStatus.EXTRACTING, DownloadStatus.INSTALLING]:
            action_button = ctk.CTkButton(
                card,
                text="Cancel",
                command=lambda sid=scenery_id: self.on_cancel(sid),
                width=80,
                height=28,
                fg_color=("#EF5350", "#C62828")
            )
            action_button.grid(row=0, column=1, rowspan=4, padx=15, pady=10)

        # Store widgets
        self.task_widgets[scenery_id] = {
            'card': card,
            'title': title_label,
            'info': info_label,
            'progress': progress_bar,
            'status': status_label,
            'action': action_button
        }

    def _update_task_card(self, task: DownloadTask):
        """Update an existing task card.

        Args:
            task: Download task
        """
        scenery_id = task.scenery.id
        if scenery_id not in self.task_widgets:
            return

        widgets = self.task_widgets[scenery_id]

        # Update status color
        status_colors = {
            DownloadStatus.QUEUED: ("gray90", "gray20"),
            DownloadStatus.DOWNLOADING: ("#E3F2FD", "#0D47A1"),
            DownloadStatus.EXTRACTING: ("#FFF3E0", "#E65100"),
            DownloadStatus.INSTALLING: ("#F3E5F5", "#6A1B9A"),
            DownloadStatus.COMPLETED: ("#E8F5E9", "#1B5E20"),
            DownloadStatus.FAILED: ("#FFEBEE", "#B71C1C"),
            DownloadStatus.CANCELLED: ("gray85", "gray25"),
        }
        widgets['card'].configure(fg_color=status_colors.get(task.status, ("gray90", "gray20")))

        # Update progress
        widgets['progress'].set(task.progress / 100.0)

        # Update status text
        widgets['status'].configure(text=self._get_status_text(task))

        # Update/remove action button based on status
        if task.status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
            if widgets['action']:
                widgets['action'].destroy()
                widgets['action'] = None

    def _get_status_text(self, task: DownloadTask) -> str:
        """Get status text for a task.

        Args:
            task: Download task

        Returns:
            Status text string
        """
        status_texts = {
            DownloadStatus.QUEUED: "⏳ Queued",
            DownloadStatus.DOWNLOADING: f"⬇️ Downloading... {task.progress:.0f}%",
            DownloadStatus.EXTRACTING: "📦 Extracting...",
            DownloadStatus.INSTALLING: "📥 Installing...",
            DownloadStatus.COMPLETED: "✅ Completed",
            DownloadStatus.FAILED: f"❌ Failed: {task.error_message or 'Unknown error'}",
            DownloadStatus.CANCELLED: "🚫 Cancelled",
        }
        return status_texts.get(task.status, "Unknown")
