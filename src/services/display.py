from PIL import Image, ImageDraw, ImageFont
import io
import logging
import requests
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from math import log, tan, pi, cos, radians
from ..utils.formatters import format_timestamp
import time

logger = logging.getLogger(__name__)

class MapProvider:
    """Base class for map tile providers"""
    def __init__(self, name: str, url_template: str, attribution: str):
        self.name = name
        self.url_template = url_template
        self.attribution = attribution

class DisplayGenerator:
    """Service for generating e-ink display images."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.font = ImageFont.load_default()
        self.map_width = width // 2
        self.map_height = height - 60
        self.session = self._create_session()
        
        # Configure map providers in order of preference
        self.providers = [
            MapProvider(
                "OpenStreetMap",
                "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                "© OpenStreetMap contributors"
            ),
            MapProvider(
                "Stamen Terrain",
                "http://tile.stamen.com/terrain/{z}/{x}/{y}.png",
                "© Stamen Design"
            ),
            MapProvider(
                "CartoDB",
                "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
                "© CartoDB"
            )
        ]
        
        # Initialize tile cache
        self.tile_cache = {}
        self.cache_duration = 3600  # 1 hour cache
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def create_display(self, ship_data: Dict[str, Any]) -> Optional[bytes]:
        """Create a display image for the TRMNL e-ink display."""
        try:
            image = Image.new('1', (self.width, self.height), 1)
            draw = ImageDraw.Draw(image)
            
            if not ship_data or ship_data.get('connection_status') != 'connected':
                self._draw_error_state(draw, ship_data)
            else:
                # Try to get map from any available provider
                map_image = self._get_map_with_fallback(
                    float(ship_data['lat']),
                    float(ship_data['lon'])
                )
                if map_image:
                    image.paste(map_image, (0, 0))
                
                self._draw_ship_info(draw, ship_data)
                self._draw_status_bar(draw, ship_data)
            
            buffer = io.BytesIO()
            image.save(buffer, format='BMP')
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating display: {str(e)}")
            return None
    
    def _get_map_tile_key(self, provider: MapProvider, zoom: int, x: int, y: int) -> str:
        """Generate cache key for map tile."""
        return f"{provider.name}_{zoom}_{x}_{y}"
    
    def _get_cached_tile(self, key: str) -> Optional[Image.Image]:
        """Get tile from cache if available and not expired."""
        if key in self.tile_cache:
            timestamp, tile = self.tile_cache[key]
            if time.time() - timestamp < self.cache_duration:
                return tile
            else:
                del self.tile_cache[key]
        return None
    
    def _cache_tile(self, key: str, tile: Image.Image) -> None:
        """Cache a map tile."""
        self.tile_cache[key] = (time.time(), tile)
    
    def _get_map_with_fallback(self, lat: float, lon: float) -> Optional[Image.Image]:
        """Try to get map from each provider until successful."""
        zoom = 8  # Adjust based on desired detail level
        
        for provider in self.providers:
            try:
                map_image = self._fetch_map_from_provider(provider, lat, lon, zoom)
                if map_image:
                    return map_image
            except Exception as e:
                logger.error(f"Error with provider {provider.name}: {str(e)}")
                continue
        
        return self._generate_fallback_map(lat, lon)
    
    def _fetch_map_from_provider(self, provider: MapProvider, lat: float, lon: float, zoom: int) -> Optional[Image.Image]:
        """Fetch map tile from specific provider."""
        try:
            # Calculate tile coordinates
            n = 2.0 ** zoom
            lat_rad = radians(lat)
            xtile = int((lon + 180.0) / 360.0 * n)
            ytile = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
            
            # Check cache first
            cache_key = self._get_map_tile_key(provider, zoom, xtile, ytile)
            cached_tile = self._get_cached_tile(cache_key)
            if cached_tile:
                return self._process_tile(cached_tile, lat, lon)
            
            # Fetch tile if not cached
            url = provider.url_template.format(z=zoom, x=xtile, y=ytile)
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                tile = Image.open(io.BytesIO(response.content))
                self._cache_tile(cache_key, tile)
                return self._process_tile(tile, lat, lon)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from {provider.name}: {str(e)}")
            return None
    
    def _process_tile(self, tile: Image.Image, lat: float, lon: float) -> Image.Image:
        """Process a map tile for display."""
        # Resize to fit display
        map_image = tile.resize((self.map_width, self.map_height))
        
        # Convert to black and white with dithering
        map_bw = map_image.convert('1', dither=Image.FLOYDSTEINBERG)
        
        # Add ship marker
        draw = ImageDraw.Draw(map_bw)
        
        # Calculate relative position within tile
        lat_rad = radians(lat)
        y_pos = self.map_height * (1 - (lat_rad - pi/4) / (pi/2))
        x_pos = self.map_width * ((lon + 180) / 360)
        
        # Draw marker
        marker_size = 10
        x, y = int(x_pos), int(y_pos)
        draw.line([(x - marker_size, y), (x + marker_size, y)], fill=0, width=2)
        draw.line([(x, y - marker_size), (x, y + marker_size)], fill=0, width=2)
        draw.ellipse([x - marker_size, y - marker_size,
                     x + marker_size, y + marker_size], outline=0)
        
        return map_bw
    
    def _generate_fallback_map(self, lat: float, lon: float) -> Image.Image:
        """Generate basic map when no providers are available."""
        map_image = Image.new('1', (self.map_width, self.map_height), 1)
        draw = ImageDraw.Draw(map_image)
        
        # Draw border and grid
        draw.rectangle([0, 0, self.map_width-1, self.map_height-1], outline=0)
        
        # Draw grid lines
        grid_spacing = 50
        for x in range(0, self.map_width, grid_spacing):
            draw.line([(x, 0), (x, self.map_height-1)], fill=0)
        for y in range(0, self.map_height, grid_spacing):
            draw.line([(0, y), (self.map_width-1, y)], fill=0)
        
        # Add position text
        draw.text((self.map_width//2, 20),
                 f"Map Unavailable",
                 font=self.font, fill=0, anchor="mm")
        draw.text((self.map_width//2, 40),
                 f"Position: {lat:.4f}°, {lon:.4f}°",
                 font=self.font, fill=0, anchor="mm")
        
        return map_image
    
    def _draw_ship_info(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw ship information on right side of display."""
        x_start = self.width // 2 + 20
        
        # Ship name header
        draw.rectangle([x_start, 30, self.width-20, 80], fill=0)
        draw.text(
            (x_start + 10, 45),
            data['ship_name'],
            font=self.font,
            fill=1
        )
        
        # MMSI and destination
        y_pos = 100
        draw.text(
            (x_start, y_pos),
            f"MMSI: {data['mmsi']}",
            font=self.font,
            fill=0
        )
        y_pos += 30
        draw.text(
            (x_start, y_pos),
            f"Destination: {data.get('destination', 'Unknown')}",
            font=self.font,
            fill=0
        )
        
        # Navigation data
        y_pos += 50
        draw.text(
            (x_start, y_pos),
            f"Speed: {data['speed']} knots",
            font=self.font,
            fill=0
        )
        y_pos += 30
        draw.text(
            (x_start, y_pos),
            f"Course: {data['course']}°",
            font=self.font,
            fill=0
        )
        y_pos += 30
        draw.text(
            (x_start, y_pos),
            f"Position: {data['lat']}°S, {data['lon']}°W",
            font=self.font,
            fill=0
        )
    
    def _draw_status_bar(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw status bar at bottom of display."""
        draw.rectangle(
            [10, self.height-40, self.width-10, self.height-10],
            fill=0
        )
        
        timestamp = format_timestamp(data['timestamp'])
        draw.text(
            (20, self.height-30),
            f"Last Update: {timestamp}",
            font=self.font,
            fill=1
        )
    
    def _draw_error_state(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw error state when no data is available."""
        draw.rectangle([30, 30, self.width-30, 80], fill=0)
        draw.text(
            (40, 40),
            "Connection Error",
            font=self.font,
            fill=1
        )
        
        error_msg = "No connection to vessel tracking service"
        if data and data.get('error'):
            error_msg = f"Error: {data['error']}"
        
        draw.text(
            (40, 100),
            error_msg,
            font=self.font,
            fill=0
        )
        
        if data and data.get('timestamp'):
            draw.text(
                (40, 140),
                f"Last successful update: {format_timestamp(data['timestamp'])}",
                font=self.font,
                fill=0
            )