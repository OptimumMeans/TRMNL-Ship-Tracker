from PIL import Image, ImageDraw, ImageFont
import io
import logging
import requests
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from math import log, tan, pi, cos, radians
from ..utils.formatters import format_timestamp, format_eta, format_distance

logger = logging.getLogger(__name__)

class DisplayGenerator:
    """Service for generating e-ink display images."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.font = ImageFont.load_default()
        self.map_width = width // 2
        self.map_height = height - 60
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'TRMNL_Ship_Tracker/1.0',
            'Accept': 'image/png'
        })
        return session
        
    def create_display(self, ship_data: Dict[str, Any]) -> Optional[bytes]:
        """Create a display image for the TRMNL e-ink display."""
        try:
            image = Image.new('1', (self.width, self.height), 1)
            draw = ImageDraw.Draw(image)
            
            if not ship_data or ship_data.get('connection_status') != 'connected':
                self._draw_error_state(draw, ship_data)
            else:
                # Get map
                map_image = self._get_map(float(ship_data['lat']), float(ship_data['lon']))
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

    def _get_map(self, lat: float, lon: float) -> Optional[Image.Image]:
        """Get map for the specified coordinates."""
        try:
            # Calculate zoom level based on current location
            zoom = 9  # Adjusted for better detail

            # Calculate tile coordinates
            lat_rad = radians(lat)
            n = 2.0 ** zoom
            xtile = int((lon + 180.0) / 360.0 * n)
            ytile = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)

            # Get surrounding tiles for better context
            tiles_to_fetch = [
                (xtile-1, ytile-1), (xtile, ytile-1), (xtile+1, ytile-1),
                (xtile-1, ytile),   (xtile, ytile),   (xtile+1, ytile),
                (xtile-1, ytile+1), (xtile, ytile+1), (xtile+1, ytile+1)
            ]

            # Create a combined image
            combined = Image.new('RGB', (256 * 3, 256 * 3))

            for idx, (x, y) in enumerate(tiles_to_fetch):
                try:
                    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        tile = Image.open(io.BytesIO(response.content))
                        pos_x = (idx % 3) * 256
                        pos_y = (idx // 3) * 256
                        combined.paste(tile, (pos_x, pos_y))
                except Exception as e:
                    logger.error(f"Error fetching tile {x},{y}: {str(e)}")
                    continue

            # Resize to our display dimensions
            resized = combined.resize((self.map_width, self.map_height), Image.LANCZOS)
            
            # Convert to black and white with dithering
            bw = resized.convert('1', dither=Image.FLOYDSTEINBERG)
            
            # Add ship marker at center
            draw = ImageDraw.Draw(bw)
            center_x = self.map_width // 2
            center_y = self.map_height // 2
            
            # Draw crosshair marker
            marker_size = 10
            draw.line([(center_x - marker_size, center_y), 
                      (center_x + marker_size, center_y)], fill=0, width=2)
            draw.line([(center_x, center_y - marker_size), 
                      (center_x, center_y + marker_size)], fill=0, width=2)
            draw.ellipse([center_x - marker_size, center_y - marker_size,
                         center_x + marker_size, center_y + marker_size], outline=0)

            return bw

        except Exception as e:
            logger.error(f"Error generating map: {str(e)}")
            return self._generate_fallback_map(lat, lon)
    
    def _generate_fallback_map(self, lat: float, lon: float) -> Image.Image:
        """Generate basic map when OpenStreetMap is unavailable."""
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
                 "OpenStreetMap Unavailable",
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
        
        # MMSI and basic info
        y_pos = 90
        draw.text(
            (x_start, y_pos),
            f"MMSI: {data['mmsi']}",
            font=self.font,
            fill=0
        )

        # Destination and ETA
        y_pos += 25
        draw.text(
            (x_start, y_pos),
            f"Destination: {data.get('destination', 'Unknown')}",
            font=self.font,
            fill=0
        )
        
        if data.get('eta_predicted') != "Unknown":
            y_pos += 20
            eta = format_eta(data['eta_predicted'])
            draw.text(
                (x_start, y_pos),
                f"ETA: {eta}",
                font=self.font,
                fill=0
            )
        
        if data.get('distance_remaining') != "Unknown":
            y_pos += 20
            distance = format_distance(data['distance_remaining'])
            draw.text(
                (x_start, y_pos),
                f"Distance: {distance}",
                font=self.font,
                fill=0
            )
        
        # Navigation data
        y_pos += 30
        draw.text(
            (x_start, y_pos),
            f"Speed: {data['speed']} knots",
            font=self.font,
            fill=0
        )
        y_pos += 25
        draw.text(
            (x_start, y_pos),
            f"Course: {data['course']}°",
            font=self.font,
            fill=0
        )
        y_pos += 25
        draw.text(
            (x_start, y_pos),
            f"Position: {data['lat']}°S, {data['lon']}°W",
            font=self.font,
            fill=0
        )

        # Navigation Status
        if data.get('nav_status'):
            y_pos += 30
            draw.text(
                (x_start, y_pos),
                f"Status: {data['nav_status']}",
                font=self.font,
                fill=0
            )

        # Vessel Dimensions
        if isinstance(data.get('dimensions'), dict):
            y_pos += 30
            dims = data['dimensions']
            draw.text(
                (x_start, y_pos),
                f"L: {dims['length']}m • W: {dims['width']}m",
                font=self.font,
                fill=0
            )
            if dims.get('draught'):
                y_pos += 20
                draw.text(
                    (x_start, y_pos),
                    f"Draught: {dims['draught']}m",
                    font=self.font,
                    fill=0
                )

        # ECA Status
        if data.get('eca_status'):
            y_pos += 25
            draw.text(
                (x_start, y_pos),
                "⬤ In Emission Control Area",
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
        source_text = f"Source: {data['source']}" if data.get('source') else ""
        status_text = f"Last Update: {timestamp} • {source_text}"
        
        draw.text(
            (20, self.height-30),
            status_text,
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