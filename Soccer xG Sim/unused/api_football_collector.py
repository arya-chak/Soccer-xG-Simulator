"""
Soccer Data Collector using API-Football
Author: Arya Chakraborty

This module retrieves soccer data including xG statistics from API-Football.
We will not be using this as API-Football does not allow free users to access xG data.
"""

import os
import json
import time
import requests
from datetime import datetime

class APIFootballCollector:
    """Class to collect soccer data from API-Football."""
    
    def __init__(self, api_key, cache_dir='data'):
        """
        Initialize the API collector.
        
        Args:
            api_key (str): Your API-Football API key
            cache_dir (str): Directory to cache API responses
        """
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
        }
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # League IDs mapping (2022-2023 season)
        self.league_ids = {
            'premier league': 39,
            'la liga': 140,
            'bundesliga': 78,
            'serie a': 135,
            'ligue 1': 61
        }
        
        # Store team IDs once retrieved
        self.team_ids = {}
    
    def _get_cached_data(self, filename):
        """Get data from cache if it exists."""
        cache_file = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Check if data has expired (older than 1 day for static data)
                if data.get('timestamp'):
                    cache_time = datetime.fromisoformat(data['timestamp'])
                    now = datetime.now()
                    # Use a longer expiry for historical data (30 days)
                    if 'historical' in filename and (now - cache_time).days < 30:
                        return data
                    # Use a shorter expiry for current data (1 day)
                    elif 'current' in filename and (now - cache_time).days < 1:
                        return data
                # Return anyway if no timestamp (for testing)
                else:
                    return data
        
        return None
    
    def _cache_data(self, filename, data):
        """Cache data to a file."""
        # Add timestamp to data
        data['timestamp'] = datetime.now().isoformat()
        
        cache_file = os.path.join(self.cache_dir, filename)
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved data to {cache_file}")
    
    def _api_request(self, endpoint, params=None):
        """
        Make a request to the API.
        
        Args:
            endpoint (str): API endpoint to request
            params (dict): Query parameters
            
        Returns:
            dict: API response data
        """
        # Construct URL
        url = f"{self.base_url}/{endpoint}"
        
        # Create cache key from endpoint and params
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items())) if params else "no_params"
        cache_filename = f"{endpoint.replace('/', '_')}_{param_str}.json"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_filename)
        if cached_data:
            print(f"Using cached data for {endpoint}")
            return cached_data
        
        # Make API request
        try:
            print(f"Making API request to {endpoint}")
            response = requests.get(url, headers=self.headers, params=params)
            
            # Check for API errors
            if response.status_code != 200:
                print(f"API Error: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            # Cache the response
            self._cache_data(cache_filename, data)
            
            # Respect rate limits
            time.sleep(1)  # Basic rate limiting
            
            return data
        
        except Exception as e:
            print(f"API request error: {e}")
            return None
    
    def get_league_id(self, league_name):
        """Get the API-Football league ID."""
        return self.league_ids.get(league_name.lower())
    
    def get_team_id(self, team_name, league_id=None):
        """
        Get the API-Football team ID.
        
        Args:
            team_name (str): Name of the team
            league_id (int, optional): ID of the league to search in
            
        Returns:
            int: Team ID if found, None otherwise
        """
        # Check if we already have the team ID cached
        if team_name.lower() in self.team_ids:
            return self.team_ids[team_name.lower()]
        
        # Search for the team
        params = {'search': team_name}
        if league_id:
            params['league'] = league_id
        
        data = self._api_request('teams', params)
        
        if data and 'response' in data and len(data['response']) > 0:
            team_id = data['response'][0]['team']['id']
            
            # Cache the team ID
            self.team_ids[team_name.lower()] = team_id
            
            return team_id
        
        print(f"Team not found: {team_name}")
        return None
    
    def get_league_standings(self, league_name, season):
        """
        Get league standings for a specific season.
        
        Args:
            league_name (str): Name of the league
            season (str): Season in format YYYY-YYYY (e.g., "2022-2023")
            
        Returns:
            dict: League standings data
        """
        # Get league ID
        league_id = self.get_league_id(league_name)
        if not league_id:
            print(f"League not found: {league_name}")
            return None
        
        # Extract season year (API uses YYYY, not YYYY-YYYY)
        season_year = season.split('-')[0]
        
        # Make API request
        params = {
            'league': league_id,
            'season': season_year
        }
        
        data = self._api_request('standings', params)
        
        if not data or 'response' not in data or len(data['response']) == 0:
            print(f"No standings data for {league_name} ({season})")
            return None
        
        return data
    
    def get_team_fixtures(self, team_name, season, league_name=None):
        """
        Get fixtures for a specific team and season.
    
        Args:
            team_name (str): Name of the team
            season (str): Season in format YYYY-YYYY
            league_name (str, optional): Name of the league
        
        Returns:
            dict: Team fixtures data
        """
        # Get league ID if provided
        league_id = None
        if league_name:
            league_id = self.get_league_id(league_name)
    
        # Get team ID
        team_id = self.get_team_id(team_name, league_id)
        if not team_id:
            print(f"Could not find team ID for {team_name}")
            return None
    
        # Extract season year
        season_year = season.split('-')[0]
    
        # Make API request
        params = {
            'team': team_id,
            'season': season_year
        }
        if league_id:
            params['league'] = league_id
    
        data = self._api_request('fixtures', params)
    
        if not data or 'response' not in data:
            print(f"No fixtures data for {team_name} ({season})")
            return None
    
        # Process the data for easier consumption
        processed_data = {
            'team': team_name,
            'season': season,
            'fixtures': []
        }
    
        for fixture in data['response']:
            # Process each fixture
            fixture_data = {
                'id': fixture['fixture']['id'],
                'date': fixture['fixture']['date'],
                'home_team': fixture['teams']['home']['name'],
                'away_team': fixture['teams']['away']['name'],
                'home_id': fixture['teams']['home']['id'],
                'away_id': fixture['teams']['away']['id'],
                'status': fixture['fixture']['status']['short'],
                'venue': fixture['fixture']['venue']['name'] if 'venue' in fixture['fixture'] else None,
                'league': fixture['league']['name'],
                'round': fixture['league']['round']
            }
        
            # Add scores if match is finished
            if fixture['fixture']['status']['short'] == 'FT':
                fixture_data['home_score'] = fixture['goals']['home']
                fixture_data['away_score'] = fixture['goals']['away']
                fixture_data['score'] = f"{fixture['goals']['home']}-{fixture['goals']['away']}"
            
                # Determine if this team won, lost, or drew
                team_is_home = fixture['teams']['home']['id'] == team_id
                team_is_away = fixture['teams']['away']['id'] == team_id
            
                if team_is_home:
                    if fixture['teams']['home']['winner'] == True:
                        fixture_data['result'] = 'W'
                    elif fixture['teams']['away']['winner'] == True:
                        fixture_data['result'] = 'L'
                    else:
                        fixture_data['result'] = 'D'
                elif team_is_away:
                    if fixture['teams']['away']['winner'] == True:
                        fixture_data['result'] = 'W'
                    elif fixture['teams']['home']['winner'] == True:
                        fixture_data['result'] = 'L'
                    else:
                        fixture_data['result'] = 'D'
        
            processed_data['fixtures'].append(fixture_data)
    
        return processed_data
    
    def get_fixture_statistics(self, fixture_id):
        """
        Get detailed statistics for a fixture including xG if available.
        
        Args:
            fixture_id (int): ID of the fixture
            
        Returns:
            dict: Fixture statistics
        """
        # Make API request
        params = {'fixture': fixture_id}
        data = self._api_request('fixtures/statistics', params)
        
        if not data or 'response' not in data:
            print(f"No statistics for fixture {fixture_id}")
            return None
        
        # Process statistics
        stats = {}
        
        for team_stats in data['response']:
            team_id = team_stats['team']['id']
            team_name = team_stats['team']['name']
            
            stats[team_id] = {
                'team_name': team_name,
                'statistics': {}
            }
            
            # Process each statistic
            for stat in team_stats['statistics']:
                stat_name = stat['type'].lower().replace(' ', '_')
                stat_value = stat['value']
                
                # Handle percentage values
                if isinstance(stat_value, str) and '%' in stat_value:
                    try:
                        stat_value = float(stat_value.replace('%', ''))
                    except:
                        pass
                
                stats[team_id]['statistics'][stat_name] = stat_value
        
        # Also get the fixture details
        fixture_data = self.get_fixture_details(fixture_id)
        if fixture_data:
            stats['fixture'] = fixture_data
        
        return stats
    
    def get_fixture_details(self, fixture_id):
        """
        Get basic details for a fixture.
        
        Args:
            fixture_id (int): ID of the fixture
            
        Returns:
            dict: Fixture details
        """
        # Make API request
        params = {'id': fixture_id}
        data = self._api_request('fixtures', params)
        
        if not data or 'response' not in data or len(data['response']) == 0:
            print(f"No details for fixture {fixture_id}")
            return None
        
        # Extract fixture details
        fixture = data['response'][0]
        
        fixture_data = {
            'id': fixture['fixture']['id'],
            'date': fixture['fixture']['date'],
            'home_team': fixture['teams']['home']['name'],
            'away_team': fixture['teams']['away']['name'],
            'home_id': fixture['teams']['home']['id'],
            'away_id': fixture['teams']['away']['id'],
            'status': fixture['fixture']['status']['short'],
            'venue': fixture['fixture']['venue']['name'] if 'venue' in fixture['fixture'] else None,
            'league': fixture['league']['name'],
            'round': fixture['league']['round']
        }
        
        # Add scores if match is finished
        if fixture['fixture']['status']['short'] == 'FT':
            fixture_data['home_score'] = fixture['goals']['home']
            fixture_data['away_score'] = fixture['goals']['away']
            fixture_data['score'] = f"{fixture['goals']['home']}-{fixture['goals']['away']}"
        
        return fixture_data
    
    def get_team_season_with_xg(self, team_name, season, league_name=None):
        """
        Get comprehensive season data for a team including fixture details and xG data.
        
        Args:
            team_name (str): Name of the team
            season (str): Season in format YYYY-YYYY
            league_name (str, optional): Name of the league
            
        Returns:
            dict: Complete team season data
        """
        # Get fixtures first
        fixtures_data = self.get_team_fixtures(team_name, season, league_name)
        if not fixtures_data:
            return None
        
        # Initialize comprehensive data
        season_data = {
            'team': team_name,
            'season': season,
            'fixtures': [],
            'stats': {
                'matches_played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'xg_for': 0,
                'xg_against': 0,
                'fixtures_with_xg': 0
            }
        }
        
        # Get detailed statistics for each fixture
        print(f"Collecting detailed statistics for {len(fixtures_data['fixtures'])} fixtures...")
        
        # Only process completed fixtures
        completed_fixtures = [f for f in fixtures_data['fixtures'] if f['status'] == 'FT']
        
        for i, fixture in enumerate(completed_fixtures):
            print(f"Processing fixture {i+1}/{len(completed_fixtures)}: {fixture['home_team']} vs {fixture['away_team']}")
            
            # Get fixture statistics including xG
            stats = self.get_fixture_statistics(fixture['id'])
            
            if stats:
                # Create comprehensive fixture data
                fixture_with_stats = fixture.copy()
                
                # Find home and away IDs
                home_id = fixture['home_id']
                away_id = fixture['away_id']
                
                # Add statistics if available
                if home_id in stats and away_id in stats:
                    fixture_with_stats['home_stats'] = stats[home_id]['statistics']
                    fixture_with_stats['away_stats'] = stats[away_id]['statistics']
                    
                    # Add xG data if available
                    home_xg = None
                    away_xg = None
                    
                    # Look for xG in various forms
                    for key in ['expected_goals', 'xg']:
                        if key in stats[home_id]['statistics'] and stats[home_id]['statistics'][key] is not None:
                            home_xg = stats[home_id]['statistics'][key]
                        if key in stats[away_id]['statistics'] and stats[away_id]['statistics'][key] is not None:
                            away_xg = stats[away_id]['statistics'][key]
                    
                    # Convert to float if possible
                    if isinstance(home_xg, str):
                        try:
                            home_xg = float(home_xg)
                        except:
                            home_xg = None
                    
                    if isinstance(away_xg, str):
                        try:
                            away_xg = float(away_xg)
                        except:
                            away_xg = None
                    
                    # Add xG to fixture data
                    fixture_with_stats['home_xg'] = home_xg
                    fixture_with_stats['away_xg'] = away_xg
                    fixture_with_stats['has_xg'] = home_xg is not None and away_xg is not None
                    
                    # Update season xG stats if xG is available
                    if fixture_with_stats['has_xg']:
                        season_data['stats']['fixtures_with_xg'] += 1
                        
                        # Add xG to season totals based on whether this team was home or away
                        if fixture['home_team'] == team_name:
                            season_data['stats']['xg_for'] += home_xg
                            season_data['stats']['xg_against'] += away_xg
                        else:
                            season_data['stats']['xg_for'] += away_xg
                            season_data['stats']['xg_against'] += home_xg
                
                # Add to fixtures list
                season_data['fixtures'].append(fixture_with_stats)
                
                # Update season stats
                season_data['stats']['matches_played'] += 1
                
                if fixture['result'] == 'W':
                    season_data['stats']['wins'] += 1
                elif fixture['result'] == 'D':
                    season_data['stats']['draws'] += 1
                elif fixture['result'] == 'L':
                    season_data['stats']['losses'] += 1
                
                # Update goals
                if fixture['home_team'] == team_name:
                    season_data['stats']['goals_for'] += fixture['home_score']
                    season_data['stats']['goals_against'] += fixture['away_score']
                else:
                    season_data['stats']['goals_for'] += fixture['away_score']
                    season_data['stats']['goals_against'] += fixture['home_score']
        
        # Calculate average xG if we have matches with xG data
        if season_data['stats']['fixtures_with_xg'] > 0:
            season_data['stats']['avg_xg_for'] = season_data['stats']['xg_for'] / season_data['stats']['fixtures_with_xg']
            season_data['stats']['avg_xg_against'] = season_data['stats']['xg_against'] / season_data['stats']['fixtures_with_xg']
            
            # Calculate xG efficiency (goals / xG)
            if season_data['stats']['xg_for'] > 0:
                season_data['stats']['xg_efficiency'] = season_data['stats']['goals_for'] / season_data['stats']['xg_for']
        
        # Save the complete data
        cache_filename = f"{team_name.lower().replace(' ', '_')}_{season.replace('-', '_')}_complete.json"
        self._cache_data(cache_filename, season_data)
        
        return season_data

# Example usage
if __name__ == "__main__":
    # Replace with your actual API key
    API_KEY = "8da19c527e9030b910931929fbe6e50f"
    
    collector = APIFootballCollector(API_KEY)
    
    # Example: Get Premier League standings
    print("Getting Premier League standings...")
    standings = collector.get_league_standings("premier league", "2022-2023")
    
    if standings:
        print("Successfully retrieved Premier League standings")
        
        # Print top teams
        if 'response' in standings and len(standings['response']) > 0:
            league_data = standings['response'][0]['league']
            print(f"\nLeague: {league_data['name']}")
            
            for i, team in enumerate(league_data['standings'][0][:5]):  # Top 5 teams
                print(f"{i+1}. {team['team']['name']} - {team['points']} points")
    
    # Example: Get Manchester United fixtures
    print("\nGetting Manchester United fixtures...")
    fixtures = collector.get_team_fixtures("Manchester United", "2022-2023", "premier league")
    
    if fixtures:
        print(f"Found {len(fixtures['fixtures'])} fixtures")
        
        # Print a few fixtures
        for i, fixture in enumerate(fixtures['fixtures'][:5]):
            print(f"\nFixture {i+1}:")
            print(f"Date: {fixture['date']}")
            print(f"Match: {fixture['home_team']} vs {fixture['away_team']}")
            if 'score' in fixture:
                print(f"Score: {fixture['score']}")
            print(f"Status: {fixture['status']}")
    
    # Example: Get detailed season data including xG
    print("\nGetting Manchester United 2022-2023 season with xG data...")
    utd_season = collector.get_team_season_with_xg("Manchester United", "2022-2023", "premier league")
    
    if utd_season:
        print(f"Successfully retrieved data for {utd_season['team']} ({utd_season['season']})")
        print(f"Matches played: {utd_season['stats']['matches_played']}")
        print(f"Record: {utd_season['stats']['wins']}-{utd_season['stats']['draws']}-{utd_season['stats']['losses']}")
        
        if 'fixtures_with_xg' in utd_season['stats'] and utd_season['stats']['fixtures_with_xg'] > 0:
            print(f"Fixtures with xG data: {utd_season['stats']['fixtures_with_xg']}")
            print(f"Average xG for: {utd_season['stats']['avg_xg_for']:.2f}")
            print(f"Average xG against: {utd_season['stats']['avg_xg_against']:.2f}")
            print(f"xG efficiency: {utd_season['stats']['xg_efficiency']:.2f}")
        
        # Print a few fixtures with xG data
        fixtures_with_xg = [f for f in utd_season['fixtures'] if f.get('has_xg', False)]
        print(f"\nFound {len(fixtures_with_xg)} fixtures with xG data")
        
        for i, fixture in enumerate(fixtures_with_xg[:5]):
            print(f"\nFixture {i+1}: {fixture['home_team']} vs {fixture['away_team']}")
            print(f"Score: {fixture['score']}")
            print(f"xG: {fixture['home_xg']} - {fixture['away_xg']}")