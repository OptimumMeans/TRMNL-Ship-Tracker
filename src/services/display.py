from PIL import Image, ImageDraw, ImageFont
import io
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from math import pi, cos, radians
from ..utils.formatters import format_timestamp

logger = logging.getLogger(__name__)

class DisplayGenerator:
    """Service for generating e-ink display images."""
    
    def __init__(self, width: int, height: int):
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
                self._draw_simple_map(draw, float(ship_data['lat']), float(ship_data['lon']))
                
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
            
    def _draw_simple_map(self, draw: ImageDraw, lat: float, lon: float) -> None:
        """Draw a simple map representation with ship position."""
        # Draw map border
        border_margin = 20
        draw.rectangle(
            [border_margin, border_margin, 
             self.map_width - border_margin, self.map_height - border_margin],
            outline=0
        )
        
        # Draw grid lines
        grid_spacing = 60  # Increased spacing for wider area
        for x in range(border_margin, self.map_width - border_margin, grid_spacing):
            draw.line([(x, border_margin), (x, self.map_height - border_margin)], fill=0, width=1)
        for y in range(border_margin, self.map_height - border_margin, grid_spacing):
            draw.line([(border_margin, y), (self.map_width - border_margin, y)], fill=0, width=1)
        
        # Calculate ship position on map
        # Map covers 60 degrees of lat/lon centered on ship position
        lat_min, lat_max = lat - 30, lat + 30
        lon_min, lon_max = lon - 30, lon + 30
        
        # Add simple geographical labels
        regions = [
            {"lat": lat_min + 10, "lon": lon_min + 10, "name": "ASIA"},
            {"lat": lat_min + 10, "lon": lon_max - 20, "name": "PACIFIC"},
            {"lat": lat_max - 10, "lon": lon_min + 20, "name": "INDIAN OCEAN"}
        ]
        
        # Add region labels
        for region in regions:
            x = border_margin + (region["lon"] - lon_min) / (lon_max - lon_min) * map_width
            y = border_margin + (lat_max - region["lat"]) / (lat_max - lat_min) * map_height
            draw.text((x, y), region["name"], font=self.font, fill=0, anchor="mm")
        
        map_height = self.map_height - (2 * border_margin)
        map_width = self.map_width - (2 * border_margin)
        
        # Convert ship position to pixel coordinates
        x = border_margin + (lon - lon_min) / (lon_max - lon_min) * map_width
        y = border_margin + (lat_max - lat) / (lat_max - lat_min) * map_height
        
        # Draw crosshair marker
        marker_size = 8
        draw.line([(x - marker_size, y), (x + marker_size, y)], fill=0, width=2)
        draw.line([(x, y - marker_size), (x, y + marker_size)], fill=0, width=2)
        draw.ellipse([x - marker_size, y - marker_size,
                     x + marker_size, y + marker_size], outline=0)
        
        # Draw coordinates
        draw.text((border_margin + 5, border_margin - 15),
                 f"{lat:.1f}°N", font=self.font, fill=0)
        draw.text((self.map_width - border_margin - 50, border_margin - 15),
                 f"{lon:.1f}°E", font=self.font, fill=0)
        
        # Draw compass rose
        compass_size = 20
        compass_x = self.map_width - compass_size - 5
        compass_y = self.map_height - compass_size - 5
        draw.text((compass_x, compass_y), "N", font=self.font, fill=0)
        draw.line([(compass_x + 8, compass_y + 15),
                  (compass_x + 8, compass_y + 5)], fill=0, width=2)
    
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
        y_pos += 30
        draw.text(
            (x_start, y_pos),
            f"Position: {data['lat']}°N, {data['lon']}°E",
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