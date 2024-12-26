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
        """Initialize the display generator."""
        self.width = width
        self.height = height
        self.font = ImageFont.load_default()
        self.map_width = width // 2  # Half width for map
        self.map_height = height - 60  # Leave space for status bar
        self.border_margin = 20
        self.usable_map_width = self.map_width - (2 * self.border_margin)
        self.usable_map_height = self.map_height - (2 * self.border_margin)
        
        # Define coastline points for Tierra del Fuego region
        self.coastline_points = [
            # Northern coast (W to E)
            (54.7, 64.0), (54.6, 65.0), (54.5, 66.0), 
            (54.4, 67.0), (54.3, 68.0), (54.2, 69.0),
            (54.1, 70.0), (54.0, 71.0), (53.9, 72.0),
            
            # Beagle Channel (W to E)
            (54.9, 66.0), (54.9, 67.0), (54.9, 68.0),
            (54.9, 69.0), (54.9, 70.0), (54.9, 71.0),
            
            # Southern coast (W to E)
            (55.2, 66.0), (55.1, 67.0), (55.0, 68.0),
            (54.9, 69.0), (54.8, 70.0), (54.7, 71.0),
            
            # Cape Horn area
            (55.8, 67.0), (55.7, 67.5), (55.6, 68.0),
            (55.5, 68.5), (55.4, 69.0)
        ]
        
        # Geographic labels
        self.regions = [
            {"lat": 54.8, "lon": 67.2, "name": "TIERRA DEL FUEGO"},
            {"lat": 54.9, "lon": 68.3, "name": "BEAGLE CHANNEL"},
            {"lat": 55.5, "lon": 66.5, "name": "DRAKE PASSAGE"}
        ]
        
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
        """Draw a simple map representation with ship position and coastlines."""
        try:
            # Calculate map coverage area (zoom level)
            lat_min, lat_max = lat - 2, lat + 2  # 4 degrees coverage
            lon_min, lon_max = lon - 3, lon + 3  # 6 degrees coverage
            
            # Draw map border
            draw.rectangle(
                [self.border_margin, self.border_margin, 
                 self.map_width - self.border_margin, 
                 self.map_height - self.border_margin],
                outline=0
            )
            
            # Draw coastlines
            for i in range(len(self.coastline_points) - 1):
                start_lat, start_lon = self.coastline_points[i]
                end_lat, end_lon = self.coastline_points[i + 1]
                
                # Convert to pixel coordinates
                start_x = self.border_margin + (
                    (start_lon - lon_min) / (lon_max - lon_min)
                ) * self.usable_map_width
                start_y = self.border_margin + (
                    (lat_max - start_lat) / (lat_max - lat_min)
                ) * self.usable_map_height
                
                end_x = self.border_margin + (
                    (end_lon - lon_min) / (lon_max - lon_min)
                ) * self.usable_map_width
                end_y = self.border_margin + (
                    (lat_max - end_lat) / (lat_max - lat_min)
                ) * self.usable_map_height
                
                # Draw coastline segment if within view
                if (lon_min <= start_lon <= lon_max and 
                    lat_min <= start_lat <= lat_max and
                    lon_min <= end_lon <= lon_max and
                    lat_min <= end_lat <= lat_max):
                    draw.line([(int(start_x), int(start_y)), 
                            (int(end_x), int(end_y))], 
                            fill=0, width=2)
            
            # Draw grid lines
            grid_spacing = 40
            for x in range(self.border_margin, self.map_width - self.border_margin, grid_spacing):
                draw.line([(x, self.border_margin), 
                        (x, self.map_height - self.border_margin)], 
                        fill=0, width=1)
            for y in range(self.border_margin, self.map_height - self.border_margin, grid_spacing):
                draw.line([(self.border_margin, y), 
                        (self.map_width - self.border_margin, y)], 
                        fill=0, width=1)
            
            # Add region labels
            for region in self.regions:
                if (lon_min <= region["lon"] <= lon_max and 
                    lat_min <= region["lat"] <= lat_max):
                    x = self.border_margin + (
                        (region["lon"] - lon_min) / (lon_max - lon_min)
                    ) * self.usable_map_width
                    y = self.border_margin + (
                        (lat_max - region["lat"]) / (lat_max - lat_min)
                    ) * self.usable_map_height
                    draw.text((int(x), int(y)), region["name"], 
                            font=self.font, fill=0, anchor="mm")
            
            # Draw ship position
            x = self.border_margin + (
                (lon - lon_min) / (lon_max - lon_min)
            ) * self.usable_map_width
            y = self.border_margin + (
                (lat_max - lat) / (lat_max - lat_min)
            ) * self.usable_map_height
            
            # Draw crosshair marker
            marker_size = 8
            x, y = int(x), int(y)
            draw.line([(x - marker_size, y), (x + marker_size, y)], 
                     fill=0, width=2)
            draw.line([(x, y - marker_size), (x, y + marker_size)], 
                     fill=0, width=2)
            draw.ellipse([x - marker_size, y - marker_size,
                         x + marker_size, y + marker_size], 
                        outline=0)
            
            # Draw coordinates
            draw.text((self.border_margin + 5, self.border_margin - 15),
                     f"{lat:.1f}°S", font=self.font, fill=0)
            draw.text((self.map_width - self.border_margin - 50, 
                      self.border_margin - 15),
                     f"{lon:.1f}°W", font=self.font, fill=0)
            
            # Draw compass rose
            compass_size = 20
            compass_x = self.map_width - compass_size - 5
            compass_y = self.map_height - compass_size - 5
            draw.text((compass_x, compass_y), "N", font=self.font, fill=0)
            draw.line([(compass_x + 8, compass_y + 15),
                      (compass_x + 8, compass_y + 5)], fill=0, width=2)
                      
        except Exception as e:
            logger.error(f"Error drawing map: {str(e)}")
            # Draw error message on map
            draw.text((self.map_width//2, self.map_height//2),
                     "Map Error", font=self.font, fill=0, anchor="mm")
    
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
            f"Position: {data['lat']}°S, {data['lon']}°W",
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