"""Main entry point for X-Plane Scenery Tool."""

import sys
import threading
from pathlib import Path

# Add src to path for imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
import zipfile
from gui.main_window import MainWindow
from gui.search_panel import SearchPanel
from gui.results_panel import ResultsPanel
from gui.details_panel import DetailsPanel
from gui.downloads_panel import DownloadsPanel
from gui.settings_panel import SettingsPanel
from core.gateway_client import GatewayClient, GatewayAPIError
from core.scenery_manager import SceneryManager, SceneryManagerError
from core.download_queue import DownloadQueue, DownloadTask, DownloadStatus
from utils.config import Config
from utils.logger import logger
from models.airport import Airport
from models.scenery import Scenery
from typing import List, Optional


class XPlaneSceneryApp:
    """Main application controller."""

    def __init__(self):
        """Initialize the application."""
        # Load configuration
        self.config = Config()

        # Create main window
        self.window = MainWindow()

        # Initialize API client and scenery manager
        self.api_client = GatewayClient()

        # Try to use configured X-Plane path first
        xplane_path = self.config.get_xplane_path()
        if xplane_path:
            xplane_path = Path(xplane_path)
            # If the user configured the Custom Scenery folder instead of the root,
            # strip it and use the parent directory
            if xplane_path.name == "Custom Scenery":
                logger.info(f"Custom Scenery folder detected in config, using parent directory")
                xplane_path = xplane_path.parent
            self.scenery_manager = SceneryManager(xplane_path=xplane_path)
        else:
            self.scenery_manager = SceneryManager()

        # Initialize download queue
        self.download_queue = DownloadQueue(
            on_task_update=self.on_download_task_update,
            process_download=self._process_download,
            max_concurrent=self.config.get('max_concurrent_downloads', 1)
        )

        # Current state
        self.current_airport: Optional[Airport] = None
        self.current_sceneries: List[Scenery] = []

        # Create panels
        self.search_panel = SearchPanel(
            self.window.container,
            on_search=self.handle_search
        )

        self.results_panel = ResultsPanel(
            self.window.container,
            on_view_details=self.show_details,
            on_back=self.show_search
        )

        self.details_panel = DetailsPanel(
            self.window.container,
            on_download=self.handle_download,
            on_back=self.show_results
        )

        self.downloads_panel = DownloadsPanel(
            self.window.container,
            on_cancel=self.cancel_download,
            on_clear=self.clear_completed_downloads
        )

        self.settings_panel = SettingsPanel(
            self.window.container,
            config=self.config,
            on_save=self.on_settings_saved
        )

        # Set up tab navigation
        self.window.set_tab_change_callback(self.on_tab_change)

        # Show search panel initially
        self.show_search()

        # Check X-Plane installation
        self.check_xplane_installation()

    def check_xplane_installation(self):
        """Check if X-Plane is installed and show status."""
        info = self.scenery_manager.get_xplane_info()

        if info['status'] == 'detected':
            self.window.set_status(
                f"X-Plane {info['version']} detected at {info['path']}",
                "success"
            )
        else:
            self.window.set_status(
                "X-Plane not detected - downloads will be available but not auto-installed",
                "warning"
            )

    def show_search(self):
        """Show the search panel."""
        self.window.show_panel(self.search_panel)
        self.window.clear_status()

    def show_results(self):
        """Show the results panel."""
        if self.current_airport:
            self.window.show_panel(self.results_panel)
            self.window.set_status(f"Found {self.current_airport.name} ({self.current_airport.icao})")

    def show_details(self, airport: Airport):
        """Show the details panel and load sceneries.

        Args:
            airport: Airport to display
        """
        self.window.set_status(f"Loading sceneries for {airport.icao}...", "info")

        # Run scenery fetch in background thread
        def fetch_sceneries_thread():
            try:
                sceneries = self.api_client.get_sceneries(
                    airport.scenery_ids,
                    include_blob=False
                )
                self.current_sceneries = sceneries

                # Update UI on main thread
                self.window.after(0, lambda: self._on_sceneries_loaded(airport, sceneries))

            except GatewayAPIError as e:
                self.window.after(0, lambda: self._on_sceneries_error(str(e)))
            except Exception as e:
                self.window.after(0, lambda: self._on_sceneries_error(f"Unexpected error: {str(e)}"))

        thread = threading.Thread(target=fetch_sceneries_thread, daemon=True)
        thread.start()

    def _on_sceneries_loaded(self, airport: Airport, sceneries: List[Scenery]):
        """Handle sceneries loaded successfully.

        Args:
            airport: Airport data
            sceneries: Loaded sceneries
        """
        self.details_panel.display_details(airport, sceneries)
        self.window.show_panel(self.details_panel)
        self.window.set_status(f"Viewing details for {airport.name} ({airport.icao})")

    def _on_sceneries_error(self, error_message: str):
        """Handle scenery loading error.

        Args:
            error_message: Error message
        """
        self.window.set_status(f"Failed to load sceneries: {error_message}", "error")

    def handle_search(self, icao: str):
        """Handle airport search.

        Args:
            icao: ICAO code to search for
        """
        self.search_panel.show_loading()
        self.window.set_status(f"Searching for {icao}...", "info")

        # Run search in background thread
        def search_thread():
            try:
                # Search for airport only (don't fetch sceneries yet)
                airport = self.api_client.search_airport(icao)
                self.current_airport = airport

                # Update UI on main thread
                self.window.after(0, lambda: self._on_search_success(airport))

            except GatewayAPIError as e:
                self.window.after(0, lambda: self._on_search_error(str(e)))
            except Exception as e:
                self.window.after(0, lambda: self._on_search_error(f"Unexpected error: {str(e)}"))

        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()

    def _on_search_success(self, airport: Airport):
        """Handle successful search.

        Args:
            airport: Retrieved airport
        """
        self.search_panel.hide_loading()
        self.search_panel.show_success(f"Found {airport.name}")

        # Show results
        self.results_panel.display_results(airport)
        self.show_results()

    def _on_search_error(self, error_message: str):
        """Handle search error.

        Args:
            error_message: Error message to display
        """
        self.search_panel.hide_loading()
        self.search_panel.show_error(error_message)
        self.window.set_status(f"Search failed: {error_message}", "error")

    def on_tab_change(self, tab: str):
        """Handle tab navigation.

        Args:
            tab: Tab name ("search", "downloads", or "settings")
        """
        if tab == "search":
            self.window.show_panel(self.search_panel)
        elif tab == "downloads":
            self.window.show_panel(self.downloads_panel)
        elif tab == "settings":
            self.window.show_panel(self.settings_panel)

    def on_settings_saved(self):
        """Handle settings being saved."""
        # Reinitialize scenery manager with new X-Plane path
        xplane_path = self.config.get_xplane_path()
        if xplane_path:
            try:
                self.scenery_manager = SceneryManager(xplane_path=Path(xplane_path))
                self.window.set_status(
                    f"Settings saved - X-Plane path updated",
                    "success"
                )
            except Exception as e:
                self.window.set_status(
                    f"Settings saved - Warning: {str(e)}",
                    "warning"
                )
        else:
            self.scenery_manager = SceneryManager()
            self.window.set_status("Settings saved", "success")

        # Recheck X-Plane installation
        self.check_xplane_installation()

    def handle_download(self, scenery: Scenery):
        """Handle scenery download by adding to queue.

        Args:
            scenery: Scenery to download
        """
        print(f"[DEBUG] handle_download called for scenery {scenery.id}", flush=True)
        logger.info(f"handle_download called for scenery {scenery.id}")

        # Add to download queue (the queue worker will process it)
        print(f"[DEBUG] Adding to download queue...", flush=True)
        added = self.download_queue.add_download(scenery)
        print(f"[DEBUG] Added: {added}", flush=True)

        if added:
            self.window.set_status(f"Added scenery {scenery.id} to download queue", "success")
            # Update badge count
            self._update_downloads_badge()
            print(f"[DEBUG] Download added to queue, worker will process it", flush=True)
        else:
            self.window.set_status(f"Scenery {scenery.id} is already in the download queue", "warning")

    def _process_download(self, scenery_id: int):
        """Process a download from the queue.

        Args:
            scenery_id: Scenery ID to download
        """
        print(f"[DEBUG] _process_download started for scenery {scenery_id}", flush=True)
        logger.info(f"Starting download process for scenery {scenery_id}")

        task = self.download_queue.get_task(scenery_id)
        if not task:
            print(f"[DEBUG] No task found for scenery {scenery_id}", flush=True)
            logger.warning(f"No task found for scenery {scenery_id}")
            return

        try:
            # Update status: Downloading
            print(f"[DEBUG] Updating status to DOWNLOADING", flush=True)
            logger.debug(f"Updating status to DOWNLOADING for scenery {scenery_id}")
            self.download_queue.update_task_status(scenery_id, DownloadStatus.DOWNLOADING, progress=10)

            # Download scenery ZIP
            print(f"[DEBUG] About to call download_scenery_zip", flush=True)
            logger.info(f"Fetching scenery ZIP from Gateway API for scenery {scenery_id}")
            zip_data = self.api_client.download_scenery_zip(scenery_id)
            print(f"[DEBUG] Received ZIP data: {len(zip_data)} bytes", flush=True)
            logger.info(f"Received ZIP data: {len(zip_data)} bytes for scenery {scenery_id}")
            self.download_queue.update_task_status(scenery_id, DownloadStatus.DOWNLOADING, progress=50)

            # Update status: Extracting
            logger.debug(f"Updating status to EXTRACTING for scenery {scenery_id}")
            self.download_queue.update_task_status(scenery_id, DownloadStatus.EXTRACTING, progress=60)

            # Check if X-Plane is detected
            xplane_info = self.scenery_manager.get_xplane_info()
            logger.info(f"X-Plane detection status: {xplane_info['status']}")
            if xplane_info['status'] == 'detected':
                # Update status: Installing
                logger.info(f"X-Plane detected, starting installation for scenery {scenery_id}")
                self.download_queue.update_task_status(scenery_id, DownloadStatus.INSTALLING, progress=80)

                # Try to install
                try:
                    logger.debug(f"Calling scenery_manager.install_scenery for scenery {scenery_id}")
                    installed = self.scenery_manager.install_scenery(task.scenery, zip_data)
                    logger.info(f"Successfully installed scenery {scenery_id} to {installed.install_path}")
                    self.download_queue.update_task_status(scenery_id, DownloadStatus.COMPLETED, progress=100)

                    # Update status bar on main thread
                    self.window.after(
                        0,
                        lambda: self.window.set_status(
                            f"✓ Scenery {scenery_id} installed to {installed.install_path}",
                            "success"
                        )
                    )
                except SceneryManagerError as e:
                    logger.error(f"Installation failed for scenery {scenery_id}: {str(e)}", exc_info=True)
                    self.download_queue.update_task_status(
                        scenery_id,
                        DownloadStatus.FAILED,
                        error_message=f"Installation failed: {str(e)}"
                    )
            else:
                # No X-Plane detected, save to downloads folder
                logger.info(f"X-Plane not detected, saving to downloads folder for scenery {scenery_id}")
                downloads_folder = Path(self.config.get_download_path())
                logger.debug(f"Download folder: {downloads_folder}")
                downloads_folder.mkdir(parents=True, exist_ok=True)

                # Check if auto-extract is enabled
                auto_extract = self.config.get_auto_extract()
                logger.info(f"Auto-extract setting: {auto_extract}")
                if auto_extract:
                    # Extract to folder
                    extract_folder = downloads_folder / f"{task.scenery.airport_icao}_{scenery_id}"
                    logger.debug(f"Creating extraction folder: {extract_folder}")
                    extract_folder.mkdir(exist_ok=True)

                    # Save ZIP temporarily
                    temp_zip = downloads_folder / f"temp_{scenery_id}.zip"
                    logger.debug(f"Saving temporary ZIP to: {temp_zip}")
                    with open(temp_zip, 'wb') as f:
                        f.write(zip_data)
                    logger.info(f"Temporary ZIP saved: {temp_zip.stat().st_size} bytes")

                    # Extract
                    try:
                        logger.info(f"Extracting ZIP to {extract_folder}")
                        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                            zip_ref.extractall(extract_folder)
                        logger.info(f"Extraction completed for scenery {scenery_id}")

                        # Remove temporary ZIP
                        temp_zip.unlink()
                        logger.debug(f"Removed temporary ZIP: {temp_zip}")

                        self.download_queue.update_task_status(scenery_id, DownloadStatus.COMPLETED, progress=100)
                        self.window.after(
                            0,
                            lambda path=str(extract_folder): self.window.set_status(
                                f"✓ Scenery {scenery_id} extracted to {path}",
                                "success"
                            )
                        )
                    except Exception as e:
                        # If extraction fails, keep the ZIP
                        logger.error(f"Extraction failed for scenery {scenery_id}: {str(e)}", exc_info=True)
                        fallback_zip = downloads_folder / f"{task.scenery.airport_icao}_{scenery_id}.zip"
                        temp_zip.rename(fallback_zip)
                        logger.info(f"Kept ZIP file as fallback: {fallback_zip}")
                        self.download_queue.update_task_status(
                            scenery_id,
                            DownloadStatus.FAILED,
                            error_message=f"Extraction failed: {str(e)}"
                        )
                else:
                    # Just save ZIP file
                    logger.info(f"Saving ZIP file without extraction for scenery {scenery_id}")
                    zip_filename = f"{task.scenery.airport_icao}_{scenery_id}.zip"
                    zip_path = downloads_folder / zip_filename
                    logger.debug(f"ZIP path: {zip_path}")

                    with open(zip_path, 'wb') as f:
                        f.write(zip_data)
                    logger.info(f"ZIP saved: {zip_path.stat().st_size} bytes")

                    self.download_queue.update_task_status(scenery_id, DownloadStatus.COMPLETED, progress=100)
                    self.window.after(
                        0,
                        lambda path=str(zip_path): self.window.set_status(
                            f"✓ Scenery {scenery_id} saved to {path}",
                            "success"
                        )
                    )

        except GatewayAPIError as e:
            logger.error(f"Gateway API error for scenery {scenery_id}: {str(e)}", exc_info=True)
            self.download_queue.update_task_status(
                scenery_id,
                DownloadStatus.FAILED,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error for scenery {scenery_id}: {str(e)}", exc_info=True)
            self.download_queue.update_task_status(
                scenery_id,
                DownloadStatus.FAILED,
                error_message=f"Unexpected error: {str(e)}"
            )
        finally:
            logger.info(f"Download process completed for scenery {scenery_id}")
            # Update badge count
            self.window.after(0, self._update_downloads_badge)

    def cancel_download(self, scenery_id: int):
        """Cancel a download.

        Args:
            scenery_id: Scenery ID to cancel
        """
        self.download_queue.cancel_download(scenery_id)
        self.window.set_status(f"Cancelled download of scenery {scenery_id}", "info")
        self._update_downloads_badge()

    def clear_completed_downloads(self):
        """Clear completed downloads from the queue."""
        self.download_queue.clear_completed()
        self.downloads_panel.clear_all_tasks()
        self._update_downloads_badge()
        self.window.set_status("Cleared completed downloads", "info")

    def on_download_task_update(self, task: DownloadTask):
        """Handle download task updates.

        Args:
            task: Updated task
        """
        print(f"[DEBUG] on_download_task_update: Called for scenery {task.scenery.id}, status={task.status}", flush=True)
        # Update UI on main thread
        print(f"[DEBUG] on_download_task_update: Calling window.after", flush=True)
        self.window.after(0, lambda: self.downloads_panel.update_task(task))
        print(f"[DEBUG] on_download_task_update: window.after returned", flush=True)

    def _update_downloads_badge(self):
        """Update the downloads tab badge count."""
        # Count active downloads
        active_count = sum(
            1 for task in self.download_queue.get_all_tasks()
            if task.status in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING,
                              DownloadStatus.EXTRACTING, DownloadStatus.INSTALLING]
        )
        self.window.update_downloads_badge(active_count)


    def run(self):
        """Start the application."""
        self.window.mainloop()

    def cleanup(self):
        """Clean up resources."""
        self.api_client.close()


def main():
    """Main entry point."""
    app = XPlaneSceneryApp()
    try:
        app.run()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
