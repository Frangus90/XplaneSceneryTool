"""Airport data model for X-Plane Scenery Gateway."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Airport:
    """Represents an airport from the X-Plane Scenery Gateway."""

    icao: str
    name: str
    latitude: float
    longitude: float
    scenery_ids: List[int]
    recommended_scenery_id: Optional[int]
    last_updated: Optional[str] = None  # Date of most recent scenery update

    @classmethod
    def from_api_response(cls, data: dict) -> 'Airport':
        """Create an Airport instance from API response data.

        Args:
            data: Dictionary containing airport data from Gateway API

        Returns:
            Airport instance
        """
        # Check if data is wrapped in an 'airport' key
        airport_data = data.get('airport', data)

        # Extract scenery IDs from the scenery list
        scenery_list = airport_data.get('scenery', [])
        scenery_ids = [s['sceneryId'] for s in scenery_list]

        # Find the most recent update date from scenery packs
        last_updated = None
        if scenery_list:
            dates = []
            for s in scenery_list:
                if s.get('dateApproved'):
                    dates.append(s['dateApproved'])
                elif s.get('dateAccepted'):
                    dates.append(s['dateAccepted'])
            if dates:
                last_updated = max(dates)

        return cls(
            icao=airport_data.get('icao', ''),
            name=airport_data.get('airportName', ''),
            latitude=airport_data.get('latitude', 0.0),
            longitude=airport_data.get('longitude', 0.0),
            scenery_ids=scenery_ids,
            recommended_scenery_id=airport_data.get('recommendedSceneryId'),
            last_updated=last_updated
        )
