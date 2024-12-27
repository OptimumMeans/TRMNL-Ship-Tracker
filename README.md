# TRMNL Ship Tracker

A TRMNL plugin for tracking ships using the VesselFinder API. This plugin displays real-time ship position, speed, course, and other relevant data on your TRMNL e-ink display.

![image](https://github.com/user-attachments/assets/3f10afde-4809-486c-8db9-c17f82b6298f)

## Features

- Real-time ship position tracking
- Speed and course display
- Automatic refresh at configurable intervals
- E-ink optimized display
- Error handling and connection status

## Prerequisites

- Python 3.12+
- TRMNL device and API key
- VesselFinder API key
- Docker (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ship-tracker.git
cd ship-tracker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create .env file:
```bash
cp .env.template .env
```

5. Update .env with your configuration:
```
VESSELFINDER_API_KEY=your_api_key_here
TRMNL_API_KEY=your_trmnl_api_key_here
TRMNL_PLUGIN_UUID=your_plugin_uuid_here
```

## Running the Application

### Development
```bash
python -m src.app
```

### Production
```bash
gunicorn src.app:app
```

## Configuration

Update the following variables in your .env file:

- `MMSI`: Ship's MMSI number to track
- `REFRESH_INTERVAL`: How often to update the display (in seconds)
- `DISPLAY_WIDTH`, `DISPLAY_HEIGHT`: Display dimensions
- API keys and credentials

## Development

### Project Structure
```
ship-tracker/
├── src/               # Application source
│   ├── services/     # Core services
│   ├── templates/    # Display templates
│   └── utils/        # Utility functions
└── tests/            # Test files
```

### Adding New Features

1. Create new service in `src/services/`
2. Update display template in `src/templates/components/`
3. Add configuration to `src/config.py`
4. Update main app in `src/app.py`

## Deployment

Deploy using render.yaml configuration:

```bash
render deploy
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT
