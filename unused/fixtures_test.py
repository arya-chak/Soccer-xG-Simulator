"""
Fixtures Test
Author: Arya Chakraborty

Test fixture statistics retrieval from API-Football
"""

import requests
import json
import os

# Your API key
API_KEY = "8da19c527e9030b910931929fbe6e50f"

# API settings
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
}

# Create a data directory if it doesn't exist
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Get Premier League ID for the 2022-2023 season
def get_premier_league_fixtures():
    print("Getting Premier League fixtures for 2022-2023 season...")
    
    url = f"{BASE_URL}/fixtures"
    params = {
        'league': 39,  # Premier League
        'season': 2022  # 2022-2023 season
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        # Save the response to a file
        with open(os.path.join(DATA_DIR, 'premier_league_fixtures_2022.json'), 'w') as f:
            json.dump(data, f, indent=2)
        
        if 'response' in data:
            fixtures = data['response']
            print(f"Found {len(fixtures)} fixtures")
            
            # Return 5 completed fixtures
            completed_fixtures = [f for f in fixtures if f['fixture']['status']['short'] == 'FT']
            return completed_fixtures[:5]
    
    return None

# Get statistics for a fixture
def get_fixture_statistics(fixture_id):
    print(f"Getting statistics for fixture {fixture_id}...")
    
    url = f"{BASE_URL}/fixtures/statistics"
    params = {
        'fixture': fixture_id
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        # Save the response to a file
        with open(os.path.join(DATA_DIR, f'fixture_{fixture_id}_statistics.json'), 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    
    return None

# Main function
def main():
    # Get some Premier League fixtures
    fixtures = get_premier_league_fixtures()
    
    if not fixtures:
        print("Could not retrieve fixtures")
        return
    
    # Print fixture details
    print("\nFixture Details:")
    for i, fixture in enumerate(fixtures):
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        score = f"{fixture['goals']['home']}-{fixture['goals']['away']}"
        
        print(f"{i+1}. {home_team} vs {away_team}, Score: {score}")
        print(f"   Date: {fixture['fixture']['date']}")
        print(f"   Fixture ID: {fixture['fixture']['id']}")
    
    # Get statistics for the first fixture
    if fixtures:
        fixture = fixtures[0]
        fixture_id = fixture['fixture']['id']
        
        print(f"\nGetting statistics for {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}...")
        
        stats = get_fixture_statistics(fixture_id)
        
        if stats and 'response' in stats:
            print("Successfully retrieved statistics")
            
            # Check for xG data
            xg_found = False
            
            for team_stats in stats['response']:
                team_name = team_stats['team']['name']
                print(f"\nStatistics for {team_name}:")
                
                for stat in team_stats['statistics']:
                    stat_name = stat['type']
                    stat_value = stat['value']
                    
                    # Print all stats
                    print(f"  {stat_name}: {stat_value}")
                    
                    # Check if xG is available
                    if stat_name in ['Expected goals', 'xG']:
                        xg_found = True
            
            if not xg_found:
                print("\nNo xG data found for this fixture")
        else:
            print("Could not retrieve statistics")

if __name__ == "__main__":
    main()