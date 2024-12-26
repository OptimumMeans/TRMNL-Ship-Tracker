from PIL import Image, ImageDraw, ImageFont
import io
import logging
import requests
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from math import log, tan, pi
from ..utils.formatters import format_timestamp

logger = logging.getLogger(__name__)

class DisplayGenerator:
    """Service for generating e-ink display images."""
    
    def __init__(self, width: int, height: int):
        """Initialize the display generator.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
        """
        self.width = width
        self.height = height
        self.font = ImageFont.load_default()
        self.map_width = width // 2  # Half width for map
        self.map_height = height - 60  # Leave space for status bar
        
    def create_display(self, ship_data: Dict[str, Any]) -> Optional[bytes]:
        """Create a display image for the TRMNL e-ink display."""
        try:
            # Create new blank image (1-bit color mode for e-ink)
            image = Image.new('1', (self.width, self.height), 1)
            draw = ImageDraw.Draw(image)
            
            if not ship_data or ship_data.get('connection_status') != 'connected':
                self._draw_error_state(draw, ship_data)
            else:
                # Draw left side with map
                map_image = self._generate_map(
                    float(ship_data['lat']),
                    float(ship_data['lon'])
                )
                if map_image:
                    image.paste(map_image, (0, 0))
                
                # Draw right side with ship data
                self._draw_ship_info(draw, ship_data)
                
                # Draw status bar
                self._draw_status_bar(draw, ship_data)
            
            # Convert to BMP format
            buffer = io.BytesIO()
            image.save(buffer, format='BMP')
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating display: {str(e)}")
            return None
    
    def _generate_map(self, lat: float, lon: float) -> Optional[Image.Image]:
        """Generate map tile with ship position."""
        try:
            # Calculate OSM tile coordinates
            zoom = 8  # Adjust zoom level as needed
            x, y = self._latlon_to_tile(lat, lon, zoom)
            
            # Fetch map tile
            tile_url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
            response = requests.get(tile_url, timeout=5)
            if response.status_code != 200:
                logger.error(f"Failed to fetch map tile: {response.status_code}")
                return None
            
            # Load and resize tile
            tile = Image.open(io.BytesIO(response.content))
            map_image = tile.resize((self.map_width, self.map_height))
            
            # Convert to black and white with dithering
            map_bw = map_image.convert('1', dither=Image.FLOYDSTEINBERG)
            
            # Add ship marker
            draw = ImageDraw.Draw(map_bw)
            pixel_x, pixel_y = self._latlon_to_pixels(lat, lon, zoom)
            marker_size = 10
            draw.ellipse(
                [pixel_x - marker_size, pixel_y - marker_size,
                 pixel_x + marker_size, pixel_y + marker_size],
                fill=0
            )
            
            return map_bw
            
        except Exception as e:
            logger.error(f"Error generating map: {str(e)}")
            return None
    
    def _latlon_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Convert latitude/longitude to tile coordinates."""
        lat_rad = lat * pi / 180
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
        return x, y
    
    def _latlon_to_pixels(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Convert latitude/longitude to pixel coordinates within map image."""
        x, y = self._latlon_to_tile(lat, lon, zoom)
        pixel_x = int((lon + 180) / 360 * self.map_width)
        pixel_y = int((1 - (log(tan(pi/4 + lat*pi/360)) / pi)) / 2 * self.map_height)
        return pixel_x, pixel_y
    
    def _draw_ship_info(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw ship information on right side of display."""
        # Start x position for right side
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
    
    def _draw_status_bar(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw status bar at bottom of display."""
        # Status bar background
        draw.rectangle(
            [10, self.height-40, self.width-10, self.height-10],
            fill=0
        )
        
        # Format timestamp
        timestamp = format_timestamp(data['timestamp'])
        
        # Status text in white
        draw.text(
            (20, self.height-30),
            f"Last Update: {timestamp}",
            font=self.font,
            fill=1
        )
    
    def _draw_error_state(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw error state when no data is available."""
        # Error title
        draw.rectangle([30, 30, self.width-30, 80], fill=0)
        draw.text(
            (40, 40),
            "Connection Error",
            font=self.font,
            fill=1
        )
        
        # Error message
        error_msg = "No connection to vessel tracking service"
        if data and data.get('error'):
            error_msg = f"Error: {data['error']}"
        
        draw.text(
            (40, 100),
            error_msg,
            font=self.font,
            fill=0
        )
        
        # Timestamp if available
        if data and data.get('timestamp'):
            draw.text(
                (40, 140),
                f"Last successful update: {format_timestamp(data['timestamp'])}",
                font=self.font,
                fill=0
            )