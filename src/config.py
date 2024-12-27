import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8080))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Ship Tracking Configuration
    MMSI = os.getenv('MMSI', '235103357')  # Sapphire Princess
    VESSELFINDER_API_KEY = os.getenv('VESSELFINDER_API_KEY')
    REFRESH_INTERVAL = int(os.getenv('REFRESH_INTERVAL', '21600'))  # 6 hour refresh int (4x/day)
    
    # TRMNL Configuration
    TRMNL_API_KEY = os.getenv('TRMNL_API_KEY')
    TRMNL_PLUGIN_UUID = os.getenv('TRMNL_PLUGIN_UUID')
    
    # Display Configuration
    DISPLAY_WIDTH = int(os.getenv('DISPLAY_WIDTH', '800'))
    DISPLAY_HEIGHT = int(os.getenv('DISPLAY_HEIGHT', '480'))
    
    # Cache Configuration
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '600'))  # 10 minutes
    
    # API Configuration
    VESSELFINDER_API_URL = 'https://api.vesselfinder.com/vessels'
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required_keys = [
            'VESSELFINDER_API_KEY',
            'TRMNL_API_KEY',
            'TRMNL_PLUGIN_UUID'
        ]
        
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_keys)}"
            )