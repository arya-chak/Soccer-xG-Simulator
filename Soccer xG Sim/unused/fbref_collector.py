"""
fbref_collector.py - Soccer Data Collector for FBRef
Author: Arya Chakraborty

This file handles fetching team statistics from FBRef.com.
It includes functions for searching teams, fetching seasonal data, and storing it locally.

This did not end up working because FBRef has a lot of anti-scraping measures in place.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
import random
from datetime import datetime

class FBRefCollector:
    def __init__(self, cache_dir='data'):
        """Initialize the collector with a cache directory."""
        self.base_url = "https://fbref.com/en/"
        self.cache_dir = cache_dir

        # creating a cache directory if one doesnt exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        # settting up session with user agent headers for proper scraping
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

        # creating dictionaory of unique IDs for teams
        self.team_ids = {}
        self._load_team_ids()

    def _load_team_ids(self):
        """Load previously cached team IDs."""
        team_ids_file = os.path.join(self.cache_dir, 'team_ids.json')

        if os.path.exists(team_ids_file):
            try:
                with open(team_ids_file, 'r') as f:
                    self.team_ids = json.load(f)
                print(f"Loaded {len(self.team_ids)} team IDs from cache")
            except Exception as e:
                print(f"Error loading team IDs: {e}")

    def _save_team_ids(self):
        """Save team IDs to cache."""
        team_ids_file = os.path.join(self.cache_dir, 'team_ids.json')

        try:
            with open(team_ids_file, 'w') as f:
                json.dump(self.team_ids, f, indent=2)
        except Exception as e:
            print(f"Error saving team IDs: {e}")

    def _get_cached_data(self, team_name, season, league):
        """Check if we have cached data for this team/season."""
        cache_file = os.path.join(self.cache_dir, f"{team_name.lower().replace(' ', '_')}_{season}_{league}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cached data: {e}")

    def _cache_data(self, team_name, season, league, data):
        """Cache the team data to a file."""
        cache_file = os.path.join(self.cache_dir, f"{team_name.lower().replace(' ', '_')}_{season}_{league}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved data to {cache_file}")
        except Exception as e:
            print(f"Error caching data: {e}")

    def search_team(self, team_name):
        """
        Search for a team on FBRef and return its ID.
        Args:
            team_name (str): The name of the team to search for    
        Returns:
            str: The team ID if found, None otherwise
        """

        # check if a team's ID is already cached
        if team_name.lower() in self.team_ids:
            print(f"Using cached team ID for {team_name}")
            return self.team_ids[team_name.lower()]
            
        print(f"Searching for team: {team_name}")

        common_teams = {
            'manchester city': 'b8fd03ef',
            'manchester united': '19538871',
            'liverpool': '822bd0ba',
            'arsenal': '18bb7c10',
            'chelsea': 'cff3d9bb',
            'tottenham': '361ca564',
            'barcelona': 'cd051869',
            'real madrid': '53a2f082',
            'bayern munich': '054efa67'
        }

        if team_name.lower() in common_teams:
            team_id = common_teams[team_name.lower()]
            print(f"Using predefined team ID for {team_name}: {team_id}")
            self.team_ids[team_name.lower()] = team_id
            self._save_team_ids()
            return team_id

        search_url = f"{self.base_url}search/search.fcgi?search={team_name.replace(' ', '+')}"

        try:
            # Respectful scraping with delay
            time.sleep(random.uniform(5, 8))
            response = self.session.get(search_url)

            if response.status_code != 200:
                print(f"Error searching for team: HTTP {response.status_code}")

                # Print more detailed error information
                print(f"Response content: {response.text[:200]}...")  # First 200 chars
                print(f"Request URL: {search_url}")
                print(f"Headers: {dict(response.request.headers)}")

                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for search results
            search_results = soup.select('div.search-item')

            for result in search_results:
                # Look for team results
                if 'team' in result.get('class', []):
                    link = result.select_one('div.search-title a')

                    if link and team_name.lower() in link.text.lower():
                        # Extract team ID from href
                        href = link['href']
                        parts = href.split('/')

                        if len(parts) >= 4:
                            team_id = parts[3]  # This should be the team ID
                            # Cache the team ID
                            self.team_ids[team_name.lower()] = team_id
                            self._save_team_ids()
                            return team_id
                
            print(f"Could not find team ID for {team_name}")
            return None
            
        except Exception as e:
            print(f"Error searching for team: {e}")
            return None
        
    def get_team_data(self, team_name, season="2022-2023", league="EPL", force_refresh=False):
        """
        Get team statistics from FBRef.
        Args:
            team_name (str): Name of the team (e.g., "Manchester United")
            season (str): Season to get data for (e.g., "2022-2023")
            league (str): League identifier (e.g., "EPL")
            force_refresh (bool): If True, ignores cache and fetches fresh data   
        Returns:
            dict: Dictionary with team statistics or None if failed
        """

        # Normalize team name for cache lookup
        normalized_team_name = team_name.lower().replace(' ', '_')

        # Check cache first
        if not force_refresh:
            cached_data = self._get_cached_data(normalized_team_name, season, league)

            if cached_data:
                print(f"Using cached data for {team_name} ({season})")
                return cached_data
            
        print(f"Fetching data for {team_name} ({season}, {league})")
        # Find team ID
        team_id = self.search_team(team_name)

        if not team_id:
            print(f"Could not find team ID for {team_name}")
            return None
        
        # Construct team page URL
        team_url = f"{self.base_url}squads/{team_id}/{season}/{team_name.replace(' ', '-')}-Stats"

        try:
            # Respectful scraping with delay
            time.sleep(random.uniform(3, 5))
            # Fetch team page
            response = self.session.get(team_url)

            if response.status_code != 200:
                print(f"Error fetching team page: HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract basic team info
            team_data = {
                'team_name': team_name,
                'season': season,
                'league': league,
                'team_id': team_id,
                'url': team_url,
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'stats': {},
                'matches': []
            }

            # Extract standard stats
            stats_tables = {
                'standard': 'stats_squads_standard_for',
                'goalkeeping': 'stats_squads_keeper_for',
                'shooting': 'stats_squads_shooting_for',
                'passing': 'stats_squads_passing_for',
                'possession': 'stats_squads_possession_for',
                'misc': 'stats_squads_misc_for'
            }

            for stat_type, table_id in stats_tables.items():
                stats_table = soup.find('table', {'id': table_id})

                if stats_table:
                    team_data['stats'][stat_type] = self._extract_team_stats(stats_table, team_name)

            # Extract match logs
            matches_table = soup.find('table', {'id': 'matchlogs_for'})

            if not matches_table:
                # Try alternative table IDs
                matches_table = soup.find('table', {'id': 'matchlogs_all'})
                
            if matches_table:
                team_data['matches'] = self._extract_match_logs(matches_table)
            
            # Cache the data
            self._cache_data(normalized_team_name, season, league, team_data)
            return team_data
        
        except Exception as e:
            print(f"Error fetching team data: {e}")
            return None
        
    def _extract_team_stats(self, table, team_name):
        """
        Extract team statistics from a stats table.
        Args:
            table (BeautifulSoup object): The table to extract data from
            team_name (str): Name of the team  
        Returns:
            dict: Dictionary of stats
        """

        stats = {}

        try:
            # Find the header row to get stat names
            header_cells = table.select('thead th')
            headers = []

            for cell in header_cells:
                stat_name = cell.get('data-stat', '')

                if stat_name:
                    headers.append(stat_name)
                
            # Find the team's row in the table
            team_row = None
            tbody = table.select_one('tbody')

            if tbody:
                rows = tbody.select('tr')

                for row in rows:
                    # Teams are typically identified in a th element
                    team_cell = row.select_one('th[data-stat="squad"]')

                    if team_cell and team_name.lower() in team_cell.text.strip().lower():
                        team_row = row
                        break

            if not team_row:
                print(f"Could not find {team_name} in the stats table")
                return stats
            
            # Extract stats from the row
            cells = team_row.select('td, th')

            for i, cell in enumerate(cells):
                if i < len(headers):
                    stat_name = headers[i]
                    stat_value = cell.text.strip()

                    # Convert to appropriate type
                    if stat_name in ['goals', 'goals_against', 'points', 'mp', 'wins', 'draws', 'losses']:
                        stats[stat_name] = int(stat_value) if stat_value.isdigit() else 0
                    elif stat_name in ['xg', 'xga', 'xg_diff', 'npxg', 'poss']:
                        try:
                            stats[stat_name] = float(stat_value) if stat_value else 0.0
                        except ValueError:
                            stats[stat_name] = 0.0
                    else:
                        stats[stat_name] = stat_value
                    
        except Exception as e:
            print(f"Error extracting team stats: {e}")
        
        return stats
    
    def _extract_match_logs(self, table):
        """
        Extract match logs from the matches table.
        Args:
            table (BeautifulSoup object): The table containing match data    
        Returns:
            list: List of match dictionaries
        """

        matches = []

        try:
            # Get header row to map column indices to names
            headers = []
            header_cells = table.select('thead th')

            for cell in header_cells:
                stat_name = cell.get('data-stat', '')

                if stat_name:
                    headers.append(stat_name)

            # Extract match data
            tbody = table.select_one('tbody')

            if tbody:
                for row in tbody.select('tr'):
                    # Skip non-match rows (spacers, etc.)
                    if 'class' in row.attrs and any(c in row['class'] for c in ['spacer', 'thead']):
                        continue

                    match_data = {} 
                    # Get all cells
                    cells = row.select('th, td')

                    # Map cells to headers
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            stat_name = headers[i]
                            stat_value = cell.text.strip()
                            
                            # Convert to appropriate type
                            if stat_name in ['goals', 'goals_against', 'shots', 'shots_on_target', 'sca', 'gca']:
                                match_data[stat_name] = int(stat_value) if stat_value and stat_value.isdigit() else 0
                            
                            elif stat_name in ['xg', 'xg_against', 'poss', 'npxg']:
                                try:
                                    match_data[stat_name] = float(stat_value) if stat_value else 0.0
                                except ValueError:
                                    match_data[stat_name] = 0.0
                            
                            else:
                                match_data[stat_name] = stat_value

                    # Only add matches with reasonable data
                    if match_data and 'date' in match_data:
                        matches.append(match_data)

        except Exception as e:
            print(f"Error extracting match logs: {e}")
        
        return matches

    def list_available_teams(self):
        """List all teams available in the cache."""

        teams = []
        
        if not os.path.exists(self.cache_dir):
            return teams
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json') and filename != 'team_ids.json':
                # Filename format: team_name_season_league.json
                parts = filename[:-5].split('_')

                if len(parts) >= 3:
                    league = parts[-1]
                    season = parts[-2]
                    team_name = '_'.join(parts[:-2]).replace('_', ' ').title()
                    teams.append({
                        'team_name': team_name,
                        'season': season,
                        'league': league
                    })

        return sorted(teams, key=lambda x: (x['team_name'], x['season']))

# Test the collector if run directly
if __name__ == "__main__":
    collector = FBRefCollector()
    time.sleep(5)  # Wait 5 seconds before starting
    # Test with a well-known team
    team_data = collector.get_team_data("Manchester United", "2022-2023", "EPL")    

    if team_data:
        print("\nTeam statistics:")

        if 'stats' in team_data and 'standard' in team_data['stats']:
            stats = team_data['stats']['standard']
            print(f"  Matches: {stats.get('mp', 'N/A')}")
            print(f"  Goals: {stats.get('goals', 'N/A')}")
            print(f"  xG: {stats.get('xg', 'N/A')}")

        print(f"\nTotal matches: {len(team_data.get('matches', []))}")          

        if team_data.get('matches'):
            print("\nFirst match:")

            for key, value in list(team_data['matches'][0].items())[:10]:  # Show first 10 items
                print(f"  {key}: {value}")

    # List available teams
    print("\nTeams in cache:")

    for team in collector.list_available_teams()[:5]:  # Show first 5 teams
        print(f"  {team['team_name']} ({team['season']}, {team['league']})")