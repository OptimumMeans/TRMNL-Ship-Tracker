import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tests.mock_vessel_service import MockVesselFinderService
from src.services.display import DisplayGenerator

def test_display():
    # Initialize services with mock data
    vessel_service = MockVesselFinderService()
    display_generator = DisplayGenerator(800, 480)
    
    # Get mock vessel data
    vessel_data = vessel_service.get_vessel_data()
    
    # Generate display
    image_data = display_generator.create_display(vessel_data)
    
    # Save to file for verification
    if image_data:
        output_path = os.path.join(os.path.dirname(__file__), 'test_display.bmp')
        with open(output_path, "wb") as f:
            f.write(image_data)
        print(f"Test display saved as {output_path}")
    else:
        print("Error generating display")

if __name__ == "__main__":
    test_display()