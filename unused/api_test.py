"""
API-Football Test Script
Author: Arya Chakraborty

This script verifies that the API key works and shows basic data retrieval.
"""

from api_football_collector import APIFootballCollector

# Initializing collector with API key
API_KEY = "8da19c527e9030b910931929fbe6e50f"
collector = APIFootballCollector(API_KEY)

# Test basic API connectivity by getting league information
print("Testing API connection...")
leagues = collector._api_request('leagues', {'season': '2022'})

if leagues and 'response' in leagues:
    print(f"API connection successful! Found {len(leagues['response'])} leagues.")
    
    # Show a few leagues as example
    print("\nSample leagues:")
    for i, league in enumerate(leagues['response'][:5]):
        print(f"{i+1}. {league['league']['name']} ({league['country']['name']})")
else:
    print("API connection failed. Please check your API key.")
    exit()

# Test getting Premier League data
print("\nGetting Premier League information...")
premier_league = collector._api_request('leagues', {'id': '39', 'season': '2022'})

if premier_league and 'response' in premier_league and len(premier_league['response']) > 0:
    league_info = premier_league['response'][0]['league']
    print(f"League: {league_info['name']} (ID: {league_info['id']})")
    print(f"Country: {premier_league['response'][0]['country']['name']}")
    print(f"Season: {premier_league['response'][0]['seasons'][0]['year']}")
else:
    print("Could not retrieve Premier League information")

# Test getting team data
print("\nTesting team search...")
team_name = "Manchester United"
team_data = collector._api_request('teams', {'search': team_name})

if team_data and 'response' in team_data and len(team_data['response']) > 0:
    team = team_data['response'][0]['team']
    print(f"Found team: {team['name']} (ID: {team['id']})")
    print(f"Country: {team_data['response'][0]['team']['country']}")
    print(f"Founded: {team_data['response'][0]['team']['founded']}")
    print(f"Stadium: {team_data['response'][0]['venue']['name']}")
    
    # Store the team ID for the next test
    team_id = team['id']
else:
    print(f"Could not find team: {team_name}")
    exit()

# Test getting fixtures for the team by ID directly
print("\nTesting fixture retrieval by team ID...")
fixtures_endpoint = f"fixtures"
fixtures_params = {
    'team': team_id,
    'season': '2022',
    'league': 39  # Premier League
}

fixtures_data = collector._api_request(fixtures_endpoint, fixtures_params)

if fixtures_data and 'response' in fixtures_data:
    print(f"Found {len(fixtures_data['response'])} fixtures for {team_name}")
    
    # Show a few fixtures
    print("\nSample fixtures:")
    for i, fixture in enumerate(fixtures_data['response'][:3]):
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        
        # Check if the match is finished and has a score
        if fixture['fixture']['status']['short'] == 'FT':
            home_goals = fixture['goals']['home']
            away_goals = fixture['goals']['away']
            score = f"{home_goals}-{away_goals}"
            print(f"{i+1}. {home_team} vs {away_team}, Score: {score}")
        else:
            print(f"{i+1}. {home_team} vs {away_team}, Status: {fixture['fixture']['status']['long']}")
        
        print(f"   Date: {fixture['fixture']['date']}")
else:
    print(f"Could not retrieve fixtures for {team_name}")

# Test getting statistics for a specific fixture
if fixtures_data and 'response' in fixtures_data and len(fixtures_data['response']) > 0:
    # Get the first completed fixture
    completed_fixtures = [f for f in fixtures_data['response'] if f['fixture']['status']['short'] == 'FT']
    
    if completed_fixtures:
        fixture = completed_fixtures[0]
        fixture_id = fixture['fixture']['id']
        
        print(f"\nTesting statistics retrieval for fixture ID: {fixture_id}")
        print(f"Match: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
        
        stats_data = collector._api_request('fixtures/statistics', {'fixture': fixture_id})
        
        if stats_data and 'response' in stats_data:
            print(f"Successfully retrieved statistics")
            
            # Check if xG data is available
            xg_available = False
            
            for team_stats in stats_data['response']:
                for stat in team_stats['statistics']:
                    if stat['type'] == 'Expected goals' or stat['type'] == 'xG':
                        xg_available = True
                        print(f"xG for {team_stats['team']['name']}: {stat['value']}")
            
            if not xg_available:
                print("No xG data available for this fixture")
        else:
            print("Could not retrieve statistics for this fixture")
    else:
        print("No completed fixtures found")

print("\nAPI test completed!")