"""X-Plane Scenery Gateway API client."""

import base64
import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List

try:
    from ..models.airport import Airport
    from ..models.scenery import Scenery
except ImportError:
    # Fallback for direct execution
    from models.airport import Airport
    from models.scenery import Scenery

logger = logging.getLogger("XPlaneSceneryTool")


class GatewayAPIError(Exception):
    """Custom exception for Gateway API errors."""
    pass


class GatewayClient:
    """Client for interacting with the X-Plane Scenery Gateway API."""

    BASE_URL = "https://gateway.x-plane.com/apiv1"
    REQUEST_DELAY = 1.0  # Delay between requests to be considerate of server load

    def __init__(self, timeout: int = 30):
        """Initialize the Gateway API client.

        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'XPlaneSceneryTool/1.0'
        })
        self._last_request_time = 0

    def _wait_for_rate_limit(self):
        """Ensure we don't make requests too quickly."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, endpoint: str) -> dict:
        """Make a GET request to the Gateway API.

        Args:
            endpoint: API endpoint path

        Returns:
            JSON response as dictionary

        Raises:
            GatewayAPIError: If the request fails
        """
        self._wait_for_rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise GatewayAPIError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise GatewayAPIError("Failed to connect to Gateway API. Check your internet connection.")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise GatewayAPIError(f"Resource not found: {endpoint}")
            else:
                raise GatewayAPIError(f"HTTP error {response.status_code}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise GatewayAPIError(f"Request failed: {str(e)}")
        except ValueError:
            raise GatewayAPIError("Invalid JSON response from server")

    def search_airport(self, icao: str) -> Airport:
        """Search for an airport by ICAO code.

        Args:
            icao: 3-4 letter ICAO code (e.g., "KJFK", "EGLL")

        Returns:
            Airport object with scenery information

        Raises:
            GatewayAPIError: If the airport is not found or request fails
        """
        # Validate and normalize ICAO code
        icao = icao.strip().upper()
        if not icao or len(icao) < 3 or len(icao) > 4:
            raise GatewayAPIError("ICAO code must be 3-4 letters")
        if not icao.isalpha():
            raise GatewayAPIError("ICAO code must contain only letters")

        try:
            data = self._make_request(f"airport/{icao}")
            return Airport.from_api_response(data)
        except GatewayAPIError as e:
            if "not found" in str(e).lower():
                raise GatewayAPIError(f"Airport '{icao}' not found in Gateway database")
            raise

    def get_scenery(self, scenery_id: int, include_blob: bool = False) -> Scenery:
        """Get detailed information about a scenery pack.

        Args:
            scenery_id: Unique scenery pack ID
            include_blob: If True, includes the base64-encoded ZIP file (default: False)

        Returns:
            Scenery object with detailed information

        Raises:
            GatewayAPIError: If the scenery is not found or request fails
        """
        if not isinstance(scenery_id, int) or scenery_id <= 0:
            raise GatewayAPIError("Scenery ID must be a positive integer")

        try:
            data = self._make_request(f"scenery/{scenery_id}")
            scenery = Scenery.from_api_response(data)

            # Optionally remove the large blob to save memory if not needed
            if not include_blob:
                scenery.master_zip_blob = None

            return scenery
        except GatewayAPIError as e:
            if "not found" in str(e).lower():
                raise GatewayAPIError(f"Scenery pack {scenery_id} not found")
            raise

    def get_sceneries(self, scenery_ids: List[int], include_blob: bool = False, max_workers: int = 10) -> List[Scenery]:
        """Get detailed information about multiple scenery packs in parallel.

        Args:
            scenery_ids: List of scenery pack IDs
            include_blob: If True, includes the base64-encoded ZIP files (default: False)
            max_workers: Maximum number of parallel requests (default: 10)

        Returns:
            List of Scenery objects

        Raises:
            GatewayAPIError: If any request fails
        """
        sceneries = []

        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            future_to_id = {
                executor.submit(self.get_scenery, scenery_id, include_blob): scenery_id
                for scenery_id in scenery_ids
            }

            # Collect results as they complete
            for future in as_completed(future_to_id):
                scenery_id = future_to_id[future]
                try:
                    scenery = future.result()
                    sceneries.append(scenery)
                except GatewayAPIError as e:
                    # Log error but continue with other sceneries
                    print(f"Warning: Failed to fetch scenery {scenery_id}: {e}")
                    continue

        # Sort by scenery ID to maintain consistent order
        sceneries.sort(key=lambda s: s.id)
        return sceneries

    def download_scenery_zip(self, scenery_id: int) -> bytes:
        """Download the scenery pack ZIP file.

        Args:
            scenery_id: Unique scenery pack ID

        Returns:
            Binary ZIP file data

        Raises:
            GatewayAPIError: If download fails or ZIP data is invalid
        """
        logger.info(f"Downloading scenery ZIP for ID {scenery_id}")
        # Get scenery with blob included
        logger.debug(f"Fetching scenery with blob for ID {scenery_id}")
        scenery = self.get_scenery(scenery_id, include_blob=True)

        if not scenery.master_zip_blob:
            logger.error(f"Scenery {scenery_id} has no downloadable ZIP file")
            raise GatewayAPIError(f"Scenery {scenery_id} has no downloadable ZIP file")

        # Decode base64 ZIP data
        try:
            logger.debug(f"Decoding base64 ZIP blob for scenery {scenery_id}")
            zip_data = base64.b64decode(scenery.master_zip_blob)
            if len(zip_data) == 0:
                logger.error(f"Scenery {scenery_id} ZIP file is empty after decoding")
                raise GatewayAPIError(f"Scenery {scenery_id} ZIP file is empty")
            logger.info(f"Successfully decoded ZIP for scenery {scenery_id}: {len(zip_data)} bytes")
            return zip_data
        except Exception as e:
            logger.error(f"Failed to decode scenery ZIP for {scenery_id}: {str(e)}", exc_info=True)
            raise GatewayAPIError(f"Failed to decode scenery ZIP: {str(e)}")

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
