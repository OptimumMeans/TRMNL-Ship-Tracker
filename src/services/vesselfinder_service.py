import requests
from datetime import datetime, UTC
import logging
import traceback
from typing import Optional, Dict, Any
from ..config import Config

logger = logging.getLogger(__name__)

class VesselFinderService:
    def __init__(self, api_key: str, mmsi: str):
        self.api_key = api_key
        self.mmsi = mmsi
        self.endpoint = Config.VESSELFINDER_API_URL
        self.last_update = None
        self._cached_data = None
        self._cache_timestamp = None
        
    def get_vessel_data(self) -> Optional[Dict[str, Any]]:
        """Fetch vessel data from VesselFinder API."""
        try:
            logger.info(f"Fetching data for MMSI {self.mmsi}")
            
            params = {
                "userkey": self.api_key,
                "mmsi": self.mmsi,
                "sat": 1  # Enable satellite data for distance_remaining and eta_predicted
            }
            
            logger.info(f"Making request to {self.endpoint}")
            response = requests.get(
                self.endpoint,
                params=params,
                timeout=10
            )
            
            logger.info(f"API Response Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"API error {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            if not data or len(data) == 0:
                logger.error("No data returned from API")
                return None
            
            ais_data = data[0].get("AIS", {})
            if not ais_data:
                logger.error("No AIS data in response")
                return None
            
            # Calculate vessel dimensions
            length = self._calculate_length(ais_data.get("A", 0), ais_data.get("B", 0))
            width = self._calculate_width(ais_data.get("C", 0), ais_data.get("D", 0))
            
            # Format data for display
            vessel_data = {
                "ship_name": ais_data.get("NAME", "Unknown Vessel"),
                "mmsi": ais_data.get("MMSI", self.mmsi),
                "imo": ais_data.get("IMO", "Unknown"),
                "lat": f"{abs(float(ais_data.get('LATITUDE', 0))):.4f}",
                "lon": f"{abs(float(ais_data.get('LONGITUDE', 0))):.4f}",
                "speed": f"{float(ais_data.get('SPEED', 0)):.1f}",
                "course": f"{float(ais_data.get('COURSE', 0)):.1f}",
                "heading": ais_data.get("HEADING", ""),
                "destination": ais_data.get("DESTINATION", "Unknown"),
                "eta": ais_data.get("ETA", "Unknown"),
                "eta_predicted": ais_data.get("ETA_PREDICTED", "Unknown"),
                "distance_remaining": ais_data.get("DISTANCE_REMAINING", "Unknown"),
                "draught": f"{float(ais_data.get('DRAUGHT', 0)):.1f}",
                "zone": ais_data.get("ZONE", "Unknown"),
                "timestamp": ais_data.get("TIMESTAMP"),
                "nav_status": self._format_nav_status(ais_data.get("NAVSTAT", 0)),
                "dimensions": {
                    "length": length,
                    "width": width,
                    "draught": ais_data.get("DRAUGHT", "Unknown")
                },
                "eca_status": ais_data.get("ECA", False),
                "connection_status": "connected",
                "source": ais_data.get("SRC", "Unknown"),
                "callsign": ais_data.get("CALLSIGN", "Unknown"),
                "type": ais_data.get("TYPE", "Unknown")
            }
            
            # Update cache and timestamps
            self._update_cache(vessel_data)
            self.last_update = datetime.now(UTC)
            
            logger.info(f"Successfully fetched data for {vessel_data['ship_name']}")
            return vessel_data
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def _calculate_length(self, a: int, b: int) -> int:
        """Calculate vessel length from A and B dimensions."""
        try:
            return a + b
        except (TypeError, ValueError):
            return 0

    def _calculate_width(self, c: int, d: int) -> int:
        """Calculate vessel width from C and D dimensions."""
        try:
            return c + d
        except (TypeError, ValueError):
            return 0

    def _format_nav_status(self, status_code: int) -> str:
        """Convert AIS navigation status code to human-readable string."""
        status_map = {
            0: "Under way using engine",
            1: "At anchor",
            2: "Not under command",
            3: "Restricted maneuverability",
            4: "Constrained by draught",
            5: "Moored",
            6: "Aground",
            7: "Engaged in fishing",
            8: "Under way sailing",
            15: "Not defined"
        }
        return status_map.get(status_code, "Unknown")
    
    def _update_cache(self, data: Dict[str, Any]) -> None:
        """Update the cache with new data."""
        self._cached_data = data
        self._cache_timestamp = datetime.now(UTC)
    
    def get_cached_data(self) -> Optional[Dict[str, Any]]:
        """Get cached vessel data if available and valid."""
        if self._is_cache_valid():
            return self._cached_data
        return None
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self._cache_timestamp:
            return False
            
        cache_age = (datetime.now(UTC) - self._cache_timestamp).total_seconds()
        return cache_age < Config.CACHE_TIMEOUT