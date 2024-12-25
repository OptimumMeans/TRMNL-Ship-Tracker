import requests

def test_vesselfinder_api():
    api_key = "WS-34BC70C9-C76F50"  # Your API key
    mmsi = "235103357"  # Sapphire Princess
    endpoint = "https://api.vesselfinder.com/vessels"
    
    params = {
        "userkey": api_key,
        "mmsi": mmsi
    }
    
    print(f"Testing VesselFinder API...")
    print(f"Endpoint: {endpoint}")
    print(f"MMSI: {mmsi}")
    
    try:
        response = requests.get(endpoint, params=params)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body: {response.text}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_vesselfinder_api()