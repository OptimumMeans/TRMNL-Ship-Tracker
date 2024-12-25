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
                "mmsi": self.mmsi
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
            
            # Format data for display, using actual fields from API response
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
                "draught": ais_data.get("DRAUGHT", "Unknown"),
                "zone": ais_data.get("ZONE", "Unknown"),
                "timestamp": ais_data.get("TIMESTAMP"),
                "connection_status": "connected",
                "source": ais_data.get("SRC", "Unknown")
            }
            
            # Update cache and timestamps
            self._update_cache(vessel_data)
            self.last_update = datetime.now(UTC)
            
            logger.info(f"Successfully fetched data for {vessel_data['ship_name']}")
            return vessel_data
            
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
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