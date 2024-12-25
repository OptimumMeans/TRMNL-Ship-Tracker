from datetime import datetime
from typing import Optional, Dict, Any, Union
import re

def validate_mmsi(mmsi: str) -> bool:
    """Validate MMSI number format.
    
    Args:
        mmsi: Maritime Mobile Service Identity number
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Remove any spaces or special characters
        mmsi_clean = ''.join(filter(str.isdigit, mmsi))
        
        # MMSI should be exactly 9 digits
        if len(mmsi_clean) != 9:
            return False
            
        # First three digits should be a valid MID (Maritime Identification Digits)
        mid = int(mmsi_clean[:3])
        return 200 <= mid <= 799  # Valid range for ship station identifiers
        
    except (ValueError, TypeError, AttributeError):
        return False

def validate_coordinates(lat: Union[str, float], lon: Union[str, float]) -> bool:
    """Validate geographic coordinates.
    
    Args:
        lat: Latitude value (-90 to 90)
        lon: Longitude value (-180 to 180)
        
    Returns:
        True if valid, False otherwise
    """
    try:
        lat_float = float(lat)
        lon_float = float(lon)
        
        return (
            -90 <= lat_float <= 90 and
            -180 <= lon_float <= 180
        )
    except (ValueError, TypeError):
        return False

def validate_speed(speed: Union[str, float]) -> bool:
    """Validate ship speed value.
    
    Args:
        speed: Speed in knots
        
    Returns:
        True if valid, False otherwise
    """
    try:
        speed_float = float(speed)
        # Maximum realistic ship speed ~50 knots
        return 0 <= speed_float <= 50
    except (ValueError, TypeError):
        return False

def validate_course(course: Union[str, float]) -> bool:
    """Validate course/heading value.
    
    Args:
        course: Course in degrees
        
    Returns:
        True if valid, False otherwise
    """
    try:
        course_float = float(course)
        return 0 <= course_float <= 360
    except (ValueError, TypeError):
        return False

def validate_timestamp(timestamp: str) -> bool:
    """Validate timestamp format.
    
    Args:
        timestamp: Timestamp string
        
    Returns:
        True if valid, False otherwise
    """
    # Try ISO format
    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return True
    except ValueError:
        pass
    
    # Try "YYYY-MM-DD HH:MM:SS UTC" format
    try:
        datetime.strptime(timestamp.replace(' UTC', ''), '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False

def validate_vessel_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate vessel data dictionary.
    
    Args:
        data: Dictionary containing vessel data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['ship_name', 'mmsi', 'lat', 'lon', 'speed', 'course', 'timestamp']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate MMSI
    if not validate_mmsi(data['mmsi']):
        return False, "Invalid MMSI format"
    
    # Validate coordinates
    if not validate_coordinates(data['lat'], data['lon']):
        return False, "Invalid coordinates"
    
    # Validate speed
    if not validate_speed(data['speed']):
        return False, "Invalid speed value"
    
    # Validate course
    if not validate_course(data['course']):
        return False, "Invalid course value"
    
    # Validate timestamp
    if not validate_timestamp(data['timestamp']):
        return False, "Invalid timestamp format"
    
    return True, None

def sanitize_string(input_str: str, max_length: int = 100) -> str:
    """Sanitize string input for display.
    
    Args:
        input_str: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ""
    
    # Remove any non-printable characters
    clean_str = ''.join(char for char in input_str if char.isprintable())
    
    # Remove any potential HTML/script tags
    clean_str = re.sub(r'<[^>]*>', '', clean_str)
    
    # Truncate to max length
    return clean_str[:max_length]