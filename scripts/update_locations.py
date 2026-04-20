#!/usr/bin/env python3
"""Update locations.json for the filtered harbors on the user's route."""
import json

# Load filtered harbors
with open('../data/harbors.json', 'r') as f:
    harbors = json.load(f)

# Create basic locations data
locations = []
for h in harbors:
    osm = h.get('osm', {})
    address = osm.get('address', {})

    # Extract location info
    country = address.get('country', 'Unknown')
    if country == 'Latvija':
        island = 'Latvia'
    elif country == 'Deutschland':
        island = 'Germany'
    elif country == 'España':
        island = 'Spain'
    else:
        island = country

    name = osm.get('name') or osm.get('display_name', f'Harbor {h["id"]}').split(',')[0]

    location = {
        'id': h['id'],
        'island': island,
        'name': name,
        'type': 'anchorage',
        'description': f'Visited harbor in {country}',
        'coordinates': {
            'lat': h['lat'],
            'lng': h['lon']
        },
        'windProtection': {
            'protectedFrom': [],
            'exposedTo': ['N', 'S', 'E', 'W'],
            'description': 'Wind protection data not available'
        },
        'depth': {
            'min': 2.0,
            'max': 5.0,
            'unit': 'm'
        },
        'bottomType': 'unknown',
        'holdingQuality': 'unknown',
        'overnightRecommended': True,
        'settledWeatherOnly': False,
        'approachDifficulty': 'moderate',
        'hazards': [],
        'ferryWakeSurge': False,
        'reservationNeeded': 'no',
        'costLevel': 'low',
        'services': {
            'fuel': False,
            'water': False,
            'electricity': False,
            'provisions': False,
            'repairs': False,
            'showers': False,
            'toilets': False,
            'wifi': False
        },
        'fallbackValue': 'medium'
    }
    locations.append(location)

# Update locations.json
locations_data = {
    'version': '1.0',
    'lastUpdated': '2026-04-18',
    'locations': locations
}

with open('../data/locations.json', 'w') as f:
    json.dump(locations_data, f, indent=2)

print(f'Created {len(locations)} location entries for your route')