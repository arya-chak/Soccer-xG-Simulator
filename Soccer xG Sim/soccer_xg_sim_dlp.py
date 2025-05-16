"""
Data Loader and Processor
Author: Arya Chakraborty

This file loads and processes team data from the JSON file.
"""

import json
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple

# Data loading and parsing
def load_team_data(file_path: str) -> Dict:
    """
    Load and parse the JSON file containing team data
    Args:
        file_path: Path to the JSON file
    Returns:
        Dictionary containing parsed team data
    """

    try:
        with open(file_path, 'r') as file:
            teams_data = json.load(file)
        
        print(f"Successfully loaded data for {len(teams_data['teams'])} teams")
        return teams_data
    
    except Exception as e:
        print(f"Error loading team data: {e}")
        raise

class Team:
    """
    Class to represent a soccer team and its statistics
    """

    def __init__(self, data: Dict[str, Any]):
        # Basic team info
        self.name = data['name']
        self.season = data['season']
        self.league = data['league']
        self.coach = data.get('coach', 'Unknown')
        self.notable_players = data.get('notable_players', [])
        self.notes = data.get('notes', '')
        # Extract key statistics
        stats = data['stats']
        self.matches_played = stats['matches_played']
        self.wins = stats['wins']
        self.draws = stats['draws']
        self.losses = stats['losses']
        # Goal statistics
        self.goals_for = stats['goals_for']
        self.goals_against = stats['goals_against']
        # xG statistics
        self.avg_xg_for = stats['avg_xg_for']
        self.avg_xg_against = stats['avg_xg_against']
        self.xg_efficiency = stats['xg_efficiency']
        self.defensive_efficiency = stats['defensive_efficiency']
        # Additional stats
        self.possession = stats.get('possession', 0)
        self.avg_goals_for = self.goals_for / self.matches_played
        self.avg_goals_against = self.goals_against / self.matches_played

    def get_display_name(self) -> str:
        """Return a formatted display name for the team"""

        return f"{self.name} ({self.season})"
    
    def get_stats_summary(self) -> Dict:
        """Return a dictionary with a summary of key team statistics"""

        return {
            'team': self.get_display_name(),
            'league': self.league,
            'record': f"{self.wins}W-{self.draws}D-{self.losses}L",
            'goals_record': f"{self.goals_for} scored, {self.goals_against} conceded",
            'xg_stats': {
                'avg_xg_for': round(self.avg_xg_for, 2),
                'avg_xg_against': round(self.avg_xg_against, 2),
                'xg_efficiency': round(self.xg_efficiency, 2),
                'defensive_efficiency': round(self.defensive_efficiency, 2)
            }
        }
    
    def to_dataframe_row(self):
        """Convert team stats to a format suitable for pandas DataFrame"""

        return {
            'name': self.name,
            'season': self.season,
            'league': getattr(self, 'league', ''),
            'matches_played': getattr(self, 'matches_played', 0),
            'wins': getattr(self, 'wins', 0),
            'draws': getattr(self, 'draws', 0), 
            'losses': getattr(self, 'losses', 0),
            'goals_for': getattr(self, 'goals_for', 0),
            'goals_against': getattr(self, 'goals_against', 0),
            'avg_xg_for': self.avg_xg_for,
            'avg_xg_against': self.avg_xg_against,
            'xg_efficiency': self.xg_efficiency,
            'defensive_efficiency': self.defensive_efficiency,
            'possession': getattr(self, 'possession', 0)
        }

class TeamManager:
    """
    Class to manage a collection of teams
    """

    def __init__(self):
        self.teams: List[Team] = []
        self.teams_df = None

    def load_teams(self, teams_data: Dict) -> List[Team]:
        """Load teams from JSON data"""

        self.teams = [Team(team_data) for team_data in teams_data['teams']]
        self.create_dataframe()
        return self.teams
    
    def create_dataframe(self) -> pd.DataFrame:
        """Create a pandas DataFrame from the team data for easier analysis"""

        if not self.teams:
            return pd.DataFrame()
        
        # Convert team objects to dictionary rows
        data = [team.to_dataframe_row() for team in self.teams]
        self.teams_df = pd.DataFrame(data)
        return self.teams_df
    
    def get_all_teams(self) -> List[Team]:
        """Get all teams"""
        return self.teams
    
    def find_team(self, name: str, season: str) -> Optional[Team]:
        """Find a team by name and season"""

        for team in self.teams:
            if team.name.lower() == name.lower() and team.season == season:
                return team
        return None
    
    def get_teams_by_league(self, league: str) -> List[Team]:
        """Get teams from a specific league"""

        return [team for team in self.teams if team.league.lower() == league.lower()]
    
    def get_teams_by_season(self, season: str) -> List[Team]:
        """Get teams from a specific season"""

        return [team for team in self.teams if team.season == season]
    
    def analyze_xg_statistics(self) -> Dict:
        """Analyze xG statistics across all teams"""

        if len(self.teams) == 0:
            return {}
        
        # Calculate various xG metrics
        avg_xg_for = np.mean([team.avg_xg_for for team in self.teams])
        avg_xg_against = np.mean([team.avg_xg_against for team in self.teams])
        avg_xg_efficiency = np.mean([team.xg_efficiency for team in self.teams])
        avg_defensive_efficiency = np.mean([team.defensive_efficiency for team in self.teams])
        # Calculate correlation between xG and actual goals
        xg_values = np.array([team.avg_xg_for for team in self.teams])
        goals_values = np.array([team.avg_goals_for for team in self.teams])
        correlation = np.corrcoef(xg_values, goals_values)[0, 1]
        return {
            'avg_xg_for': avg_xg_for,
            'avg_xg_against': avg_xg_against,
            'avg_xg_efficiency': avg_xg_efficiency,
            'avg_defensive_efficiency': avg_defensive_efficiency,
            'xg_goals_correlation': correlation
        }

def main():
    """Example usage of the Team and TeamManager classes"""

    try:
        # 1. Load the team data from file
        teams_data = load_team_data('teams_data.json')

        # 2. Create a team manager and load the teams
        team_manager = TeamManager()
        team_manager.load_teams(teams_data)
        
        # 3. Get all teams and display their stats
        all_teams = team_manager.get_all_teams()
        print(f"Loaded {len(all_teams)} teams")
        
        # 4. Display summary for each team
        for team in all_teams:
            print(team.get_stats_summary())
        
        # 5. Example: Find a specific team
        man_utd = team_manager.find_team("Manchester United", "2024-2025")
        
        if man_utd:
            print("\nFound team:", man_utd.get_display_name())
            print("xG For:", man_utd.avg_xg_for)
            print("xG Against:", man_utd.avg_xg_against)
            print("xG Efficiency:", man_utd.xg_efficiency)
        
        # 6. Analyze xG statistics
        xg_analysis = team_manager.analyze_xg_statistics()
        print("\nxG Analysis across all teams:")
        
        for key, value in xg_analysis.items():
            print(f"{key}: {value:.4f}")
        
        # 7. Show the DataFrame for easy data analysis
        print("\nTeams DataFrame:")
        print(team_manager.teams_df.head())
        return team_manager
    
    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    main()