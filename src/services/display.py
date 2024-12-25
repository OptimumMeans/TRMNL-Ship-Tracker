from PIL import Image, ImageDraw, ImageFont
import io
import logging
from typing import Optional, Dict, Any
from datetime import datetime
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
        
    def create_display(self, ship_data: Dict[str, Any]) -> Optional[bytes]:
        """Create a display image for the TRMNL e-ink display.
        
        Args:
            ship_data: Dictionary containing ship tracking data
            
        Returns:
            Bytes containing the BMP image data, or None if generation fails
        """
        try:
            # Create new blank image (1-bit color mode for e-ink)
            image = Image.new('1', (self.width, self.height), 1)
            draw = ImageDraw.Draw(image)
            
            if not ship_data or ship_data.get('connection_status') != 'connected':
                self._draw_error_state(draw, ship_data)
            else:
                self._draw_layout(draw, ship_data)
            
            # Convert to BMP format
            buffer = io.BytesIO()
            image.save(buffer, format='BMP')
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating display: {str(e)}")
            return None
    
    def _draw_layout(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw the main layout with ship data."""
        # Main container border
        draw.rectangle([10, 10, self.width-10, self.height-10], outline=0)
        
        # Ship info section
        self._draw_ship_info(draw, data)
        
        # Position section
        self._draw_position(draw, data)
        
        # Navigation section
        self._draw_navigation(draw, data)
        
        # Status bar
        self._draw_status_bar(draw, data)
    
    def _draw_ship_info(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw ship identification section."""
        # Header box with ship name (inverted)
        draw.rectangle([30, 30, self.width-30, 80], fill=0)
        draw.text(
            (40, 40),
            data['ship_name'],
            font=self.font,
            fill=1
        )
        
        # MMSI and destination info
        draw.text(
            (40, 90),
            f"MMSI: {data['mmsi']}",
            font=self.font,
            fill=0
        )
        draw.text(
            (40, 110),
            f"Destination: {data.get('destination', 'Unknown')}",
            font=self.font,
            fill=0
        )
    
    def _draw_position(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw position information section."""
        # Section title
        draw.text(
            (40, 150),
            "Current Position",
            font=self.font,
            fill=0
        )
        
        # Position data in boxes
        # Latitude
        draw.rectangle([40, 170, self.width//2-20, 210], outline=0)
        draw.text(
            (50, 180),
            f"Lat: {data['lat']}°S",
            font=self.font,
            fill=0
        )
        
        # Longitude
        draw.rectangle([self.width//2+20, 170, self.width-40, 210], outline=0)
        draw.text(
            (self.width//2+30, 180),
            f"Lon: {data['lon']}°W",
            font=self.font,
            fill=0
        )
    
    def _draw_navigation(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        """Draw navigation data section."""
        # Section title
        draw.text(
            (40, 230),
            "Navigation Data",
            font=self.font,
            fill=0
        )
        
        # Speed and course boxes
        # Speed
        draw.rectangle([40, 250, self.width//2-20, 290], outline=0)
        draw.text(
            (50, 260),
            f"Speed: {data['speed']} knots",
            font=self.font,
            fill=0
        )
        
        # Course
        draw.rectangle([self.width//2+20, 250, self.width-40, 290], outline=0)
        draw.text(
            (self.width//2+30, 260),
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