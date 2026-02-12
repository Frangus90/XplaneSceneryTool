"""Scenery data model for X-Plane Scenery Gateway."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Scenery:
    """Represents a scenery pack from the X-Plane Scenery Gateway."""

    id: int
    airport_icao: str
    artist_name: str
    date_uploaded: str
    date_accepted: Optional[str]
    date_approved: Optional[str]
    type: str  # "2D" or "3D"
    status: str  # "Approved", "Declined", "Pending"
    master_zip_blob: Optional[str]  # base64-encoded ZIP file
    features: List[str]
    wed_version: Optional[str]
    xplane_version: Optional[str]
    artist_comments: Optional[str]
    moderator_comments: Optional[str]
    parent_scenery_id: Optional[int]
    is_editors_choice: bool

    @classmethod
    def from_api_response(cls, data: dict, airport_icao: str = '') -> 'Scenery':
        """Create a Scenery instance from API response data.

        Args:
            data: Dictionary containing scenery data from Gateway API
            airport_icao: ICAO code of the airport (if not in data)

        Returns:
            Scenery instance
        """
        # Check if data is wrapped in a 'scenery' key
        scenery_data = data.get('scenery', data)

        # Extract features as a list
        features = []
        if scenery_data.get('features'):
            features = [f.strip() for f in str(scenery_data['features']).split(',') if f.strip()]

        return cls(
            id=scenery_data.get('sceneryId', 0),
            airport_icao=scenery_data.get('icao', airport_icao),
            artist_name=scenery_data.get('userName', 'Unknown'),
            date_uploaded=scenery_data.get('dateUploaded', ''),
            date_accepted=scenery_data.get('dateAccepted'),
            date_approved=scenery_data.get('dateApproved'),
            type=scenery_data.get('type', '2D'),
            status=scenery_data.get('Status', 'Unknown'),
            master_zip_blob=scenery_data.get('masterZipBlob'),
            features=features,
            wed_version=scenery_data.get('WEDVersion'),
            xplane_version=scenery_data.get('XPlaneVersion'),
            artist_comments=scenery_data.get('artistComments'),
            moderator_comments=scenery_data.get('moderatorComments'),
            parent_scenery_id=scenery_data.get('parentId'),
            is_editors_choice=scenery_data.get('EditorsChoice', False)
        )


@dataclass
class InstalledScenery:
    """Represents an installed scenery pack."""

    scenery_id: int
    airport_icao: str
    installed_date: str
    install_path: str
    version: str
