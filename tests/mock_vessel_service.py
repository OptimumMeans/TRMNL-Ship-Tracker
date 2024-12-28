from datetime import datetime, UTC
from typing import Optional, Dict, Any

class MockVesselFinderService:
    """Mock service for testing without API calls."""
    
    def __init__(self, api_key: str = "mock_key", mmsi: str = "235103357"):
        self.api_key = api_key
        self.mmsi = mmsi
        self.last_update = datetime.now(UTC)
        
    def get_vessel_data(self) -> Optional[Dict[str, Any]]:
        """Return mock vessel data."""
        return {
            "ship_name": "SAPPHIRE PRINCESS",
            "mmsi": "235103357",
            "imo": "9228186",
            "lat": "62.8568",
            "lon": "58.7332",
            "speed": "13.3",
            "course": "226.8",
            "heading": "225",
            "destination": "ADMIRALTY BAY",
            "eta": "2024-12-28 15:30:00",
            "eta_predicted": "2024-12-28 16:45:00",
            "distance_remaining": 120,
            "draught": "8.1",
            "nav_status": "Under way using engine",
            "dimensions": {
                "length": 288,
                "width": 38,
                "draught": 8.1
            },
            "eca_status": True,
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "connection_status": "connected",
            "source": "TER",
            "zone": "Antarctic Waters"
        }
        
    def get_cached_data(self) -> Optional[Dict[str, Any]]:
        """Return mock cached data."""
        return self.get_vessel_data()
    
    def _is_cache_valid(self) -> bool:
        """Mock cache validation."""
        return True