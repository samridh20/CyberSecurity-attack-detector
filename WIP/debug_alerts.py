#!/usr/bin/env python3
"""Debug ML Alerts"""

import requests
import json

def debug_alerts():
    try:
        response = requests.get("http://127.0.0.1:8000/alerts/recent?limit=5", timeout=5)
        
        if response.status_code == 200:
            alerts = response.json()
            print(f"Got {len(alerts)} alerts")
            
            if alerts:
                print("Alert data:")
                for alert in alerts:
                    print(json.dumps(alert, indent=2))
            else:
                print("No alerts found")
        else:
            print(f"API error: {response.status_code}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_alerts()