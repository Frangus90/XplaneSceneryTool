"""Download queue management for scenery downloads."""

import threading
import queue
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Optional
from datetime import datetime

try:
    from ..models.scenery import Scenery
except ImportError:
    from models.scenery import Scenery


class DownloadStatus(Enum):
    """Download status enumeration."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Represents a download task."""
    scenery: Scenery
    status: DownloadStatus
    progress: float  # 0-100
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class DownloadQueue:
    """Manages a queue of scenery downloads."""

    def __init__(
        self,
        on_task_update: Callable[[DownloadTask], None],
        process_download: Callable[[int], None],
        max_concurrent: int = 1
    ):
        """Initialize the download queue.

        Args:
            on_task_update: Callback when a task is updated (receives DownloadTask)
            process_download: Callback to process a download (receives scenery_id)
            max_concurrent: Maximum number of concurrent downloads (default: 1)
        """
        self.on_task_update = on_task_update
        self.process_download = process_download
        self.max_concurrent = max_concurrent

        # Task storage
        self.tasks: dict[int, DownloadTask] = {}  # scenery_id -> DownloadTask
        self.task_queue = queue.Queue()

        # Control
        self.worker_threads = []
        self.is_running = False
        self.lock = threading.Lock()

    def add_download(self, scenery: Scenery) -> bool:
        """Add a scenery to the download queue.

        Args:
            scenery: Scenery to download

        Returns:
            True if added, False if already in queue
        """
        print(f"[DEBUG] add_download: Entering method for scenery {scenery.id}", flush=True)
        print(f"[DEBUG] add_download: Acquiring lock...", flush=True)
        with self.lock:
            print(f"[DEBUG] add_download: Lock acquired", flush=True)
            # Check if already queued or downloading
            if scenery.id in self.tasks:
                print(f"[DEBUG] add_download: Scenery {scenery.id} already exists in tasks", flush=True)
                existing = self.tasks[scenery.id]
                if existing.status in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING,
                                      DownloadStatus.EXTRACTING, DownloadStatus.INSTALLING]:
                    print(f"[DEBUG] add_download: Scenery {scenery.id} already in progress", flush=True)
                    return False  # Already in progress

            # Create task
            print(f"[DEBUG] add_download: Creating DownloadTask", flush=True)
            task = DownloadTask(
                scenery=scenery,
                status=DownloadStatus.QUEUED,
                progress=0.0
            )
            print(f"[DEBUG] add_download: Task created", flush=True)
            self.tasks[scenery.id] = task
            print(f"[DEBUG] add_download: Task added to tasks dict", flush=True)

            print(f"[DEBUG] add_download: Putting scenery {scenery.id} into task_queue", flush=True)
            self.task_queue.put(scenery.id)
            print(f"[DEBUG] add_download: Task added to queue", flush=True)

            # Notify update
            print(f"[DEBUG] add_download: Calling _notify_update", flush=True)
            self._notify_update(task)
            print(f"[DEBUG] add_download: _notify_update completed", flush=True)

            # Start workers if not running
            print(f"[DEBUG] add_download: Checking if workers need to start (is_running={self.is_running})", flush=True)
            if not self.is_running:
                print(f"[DEBUG] add_download: Starting workers...", flush=True)
                # Call internal method that doesn't acquire lock (we already have it)
                self._start_workers()
                print(f"[DEBUG] add_download: Workers started", flush=True)

            print(f"[DEBUG] add_download: Returning True", flush=True)
            return True

    def start(self):
        """Start the download queue workers."""
        with self.lock:
            self._start_workers()

    def _start_workers(self):
        """Internal method to start workers. Must be called with lock held."""
        if self.is_running:
            return

        self.is_running = True

        # Start worker threads
        for _ in range(self.max_concurrent):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.worker_threads.append(worker)

    def stop(self):
        """Stop the download queue workers."""
        with self.lock:
            self.is_running = False

    def cancel_download(self, scenery_id: int):
        """Cancel a download.

        Args:
            scenery_id: ID of the scenery to cancel
        """
        with self.lock:
            if scenery_id in self.tasks:
                task = self.tasks[scenery_id]
                if task.status in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING,
                                  DownloadStatus.EXTRACTING, DownloadStatus.INSTALLING]:
                    task.status = DownloadStatus.CANCELLED
                    task.completed_at = datetime.now().isoformat()
                    self._notify_update(task)

    def get_task(self, scenery_id: int) -> Optional[DownloadTask]:
        """Get a download task by scenery ID.

        Args:
            scenery_id: Scenery ID

        Returns:
            DownloadTask or None
        """
        return self.tasks.get(scenery_id)

    def get_all_tasks(self) -> list[DownloadTask]:
        """Get all download tasks.

        Returns:
            List of all tasks
        """
        return list(self.tasks.values())

    def clear_completed(self):
        """Clear completed and failed tasks from the queue."""
        with self.lock:
            to_remove = []
            for scenery_id, task in self.tasks.items():
                if task.status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED,
                                  DownloadStatus.CANCELLED]:
                    to_remove.append(scenery_id)

            for scenery_id in to_remove:
                del self.tasks[scenery_id]

    def _worker(self):
        """Worker thread that processes downloads."""
        print(f"[DEBUG] DownloadQueue worker thread started", flush=True)
        while self.is_running:
            try:
                # Get next task (with timeout to allow checking is_running)
                print(f"[DEBUG] Worker waiting for task...", flush=True)
                scenery_id = self.task_queue.get(timeout=1)
                print(f"[DEBUG] Worker got task: {scenery_id}", flush=True)

                with self.lock:
                    if scenery_id not in self.tasks:
                        print(f"[DEBUG] Scenery {scenery_id} not in tasks", flush=True)
                        self.task_queue.task_done()
                        continue
                    task = self.tasks[scenery_id]

                    # Check if cancelled
                    if task.status == DownloadStatus.CANCELLED:
                        print(f"[DEBUG] Task {scenery_id} was cancelled", flush=True)
                        self.task_queue.task_done()
                        continue

                # Process download
                print(f"[DEBUG] Worker calling process_download for {scenery_id}", flush=True)
                self.process_download(scenery_id)
                print(f"[DEBUG] Worker finished processing {scenery_id}", flush=True)

                self.task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERROR] Worker error: {e}", flush=True)
                continue

    def update_task_status(
        self,
        scenery_id: int,
        status: DownloadStatus,
        progress: float = None,
        error_message: str = None
    ):
        """Update a task's status.

        Args:
            scenery_id: Scenery ID
            status: New status
            progress: Optional progress (0-100)
            error_message: Optional error message
        """
        with self.lock:
            if scenery_id not in self.tasks:
                return

            task = self.tasks[scenery_id]
            task.status = status

            if progress is not None:
                task.progress = progress

            if error_message:
                task.error_message = error_message

            if status == DownloadStatus.DOWNLOADING and not task.started_at:
                task.started_at = datetime.now().isoformat()

            if status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
                task.completed_at = datetime.now().isoformat()
                task.progress = 100.0 if status == DownloadStatus.COMPLETED else task.progress

            self._notify_update(task)

    def _notify_update(self, task: DownloadTask):
        """Notify that a task was updated.

        Args:
            task: Updated task
        """
        print(f"[DEBUG] _notify_update: Called for scenery {task.scenery.id}", flush=True)
        if self.on_task_update:
            print(f"[DEBUG] _notify_update: Calling callback...", flush=True)
            try:
                self.on_task_update(task)
                print(f"[DEBUG] _notify_update: Callback completed", flush=True)
            except Exception as e:
                print(f"[ERROR] Error in task update callback: {e}", flush=True)
        else:
            print(f"[DEBUG] _notify_update: No callback registered", flush=True)
