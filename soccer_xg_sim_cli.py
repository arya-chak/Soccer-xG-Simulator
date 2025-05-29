"""
Soccer xG Simulator Command Line Interface
Author: Arya Chakraborty

This is the command line interface where users can pick what teams they want to simulate.
"""

import argparse
import sys
from typing import Dict, List, Optional, Tuple
from soccer_xg_sim_dlp import load_team_data, Team, TeamManager
from xg_simulator import Match, MatchSimulator, test_simulation


def parse_arguments():
    """Parse command line arguments for the xG simulator"""
    
    parser = argparse.ArgumentParser(
        description='Soccer Match Simulator based on Expected Goals (xG)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add arguments
    parser.add_argument('--data', type=str, default='teams_data.json', help='Path to the JSON file containing team data')
    parser.add_argument('--home', type=str, help='Home team name (e.g., "Manchester United")')
    parser.add_argument('--away', type=str, help='Away team name (e.g., "Real Madrid")')
    parser.add_argument('--home-season', type=str, default="2024-2025", help='Season for home team (e.g., "2024-2025")')
    parser.add_argument('--away-season', type=str, default="2021-2022", help='Season for away team (e.g., "2021-2022")')
    parser.add_argument('--neutral', action='store_true', help='Simulate match at a neutral venue (no home advantage)')
    parser.add_argument('--simulations', type=int, default=10000, help='Number of simulations to run')
    parser.add_argument('--list-teams', action='store_true', help='List all available teams with details and exit')                   
    parser.add_argument('--brief', action='store_true', help='Show brief team listing without detailed information')
    return parser.parse_args()


def list_available_teams(team_manager: TeamManager, detailed: bool = True):
    """
    Display a list of all available teams with their details
    Args:
        team_manager: The TeamManager instance
        detailed: Whether to show detailed team information
    """

    teams = team_manager.get_all_teams()
    
    if not teams:
        print("No teams available in the dataset.")
        return
    
    print("\nAvailable Teams:")
    print("=" * 80)
    # Group teams by name for better organization
    teams_by_name: Dict[str, List[Team]] = {}
    for team in teams:
        if team.name not in teams_by_name:
            teams_by_name[team.name] = []
        teams_by_name[team.name].append(team)
    
    # Print teams organized by name
    for team_name in sorted(teams_by_name.keys()):
        print(f"\n{team_name}:")
        print("-" * 80)
        # Sort team instances by season in descending order (newest first)
        sorted_teams = sorted(teams_by_name[team_name], 
                             key=lambda t: t.season, 
                             reverse=True)
        
        for team in sorted_teams:
            print(f"  Season: {team.season}")
            
            # Display detailed team information if requested
            if detailed:
                print(f"  League: {getattr(team, 'league', 'N/A')}")
                print(f"  Coach: {getattr(team, 'coach', 'N/A')}")
                
                # Display notable players if available
                if hasattr(team, 'notable_players') and team.notable_players:
                    print(f"  Notable Players: {', '.join(team.notable_players)}")
                
                # Display team notes if available
                if hasattr(team, 'notes') and team.notes:
                    print(f"  Notes: {team.notes}")
                
                # Display key statistics
                print(f"  xG For: {team.avg_xg_for:.2f} | xG Against: {team.avg_xg_against:.2f}")
                print(f"  xG Efficiency: {team.xg_efficiency:.2f} | Defensive Efficiency: {team.defensive_efficiency:.2f}")
                
                # Add other available statistics if present
                if hasattr(team, 'record'):
                    print(f"  Record: {team.record}")
                
                if hasattr(team, 'matches_played') and hasattr(team, 'wins') and hasattr(team, 'draws') and hasattr(team, 'losses'):
                    print(f"  Record: {team.wins}W-{team.draws}D-{team.losses}L ({team.matches_played} matches)")
                
                if hasattr(team, 'goals_for') and hasattr(team, 'goals_against'):
                    print(f"  Goals: {team.goals_for} scored, {team.goals_against} conceded")
                
                if hasattr(team, 'possession'):
                    print(f"  Avg. Possession: {team.possession:.1f}%")
            
            print() # Empty line between teams


def find_team_interactive(team_manager: TeamManager, role: str = "home") -> Optional[Tuple[Team, str, str]]:
    """
    Interactive menu to find and select a team
    Args:
        team_manager: The TeamManager instance
        role: Either "home" or "away" to customize prompts
    Returns:
        Tuple of (selected team, team name, team season) or None if canceled
    """
    teams = team_manager.get_all_teams()
    
    if not teams:
        print("No teams available in the dataset.")
        return None
    
    # Get unique team names
    team_names = sorted(set(team.name for team in teams))
    # Display team name options
    print(f"\nSelect {role} team:")
    for i, name in enumerate(team_names, 1):
        print(f"{i}. {name}")
    
    print("0. Cancel")
    
    # Get user selection for team name
    while True:
        try:
            choice = int(input(f"\nEnter number for {role} team (0 to cancel): "))
            if choice == 0:
                return None
            
            if 1 <= choice <= len(team_names):
                selected_name = team_names[choice - 1]
                break
            else:
                print(f"Please enter a number between 0 and {len(team_names)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Get seasons for the selected team
    selected_team_seasons = sorted(
        [team.season for team in teams if team.name == selected_name],
        reverse=True  # Newest seasons first
    )
    
    # Display season options
    print(f"\nSelect season for {selected_name}:")
    for i, season in enumerate(selected_team_seasons, 1):
        print(f"{i}. {season}")
    
    print("0. Cancel")
    
    # Get user selection for season
    while True:
        try:
            choice = int(input(f"\nEnter number for season (0 to cancel): "))
            if choice == 0:
                return None
            
            if 1 <= choice <= len(selected_team_seasons):
                selected_season = selected_team_seasons[choice - 1]
                break
            else:
                print(f"Please enter a number between 0 and {len(selected_team_seasons)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Find and return the selected team
    selected_team = team_manager.find_team(selected_name, selected_season)
    return selected_team, selected_name, selected_season


def interactive_mode(team_manager: TeamManager):
    """
    Run the simulator in interactive mode, prompting for team selection and simulation parameters
    Args:
        team_manager: The TeamManager instance
    """

    print("\n=== Soccer xG Match Simulator ===")
    # Show all available teams with details before selection
    list_available_teams(team_manager, detailed=True)
    # Select home team
    home_result = find_team_interactive(team_manager, "home")

    if not home_result:
        print("Team selection cancelled.")
        return
    
    home_team, home_name, home_season = home_result
    # Select away team
    away_result = find_team_interactive(team_manager, "away")

    if not away_result:
        print("Team selection cancelled.")
        return
    
    away_team, away_name, away_season = away_result
    
    # Confirm selection
    print(f"\nSelected Match: {home_name} ({home_season}) vs {away_name} ({away_season})")
    # Select venue type
    venue_options = ["Home/Away (with home advantage)", "Neutral venue (no advantage)"]
    print("\nSelect venue type:")

    for i, option in enumerate(venue_options, 1):
        print(f"{i}. {option}")
    
    venue_choice = 0
    while venue_choice < 1 or venue_choice > len(venue_options):
        try:
            venue_choice = int(input("\nEnter number for venue type: "))
            if venue_choice < 1 or venue_choice > len(venue_options):
                print(f"Please enter a number between 1 and {len(venue_options)}")
        except ValueError:
            print("Please enter a valid number")
    
    neutral_venue = (venue_choice == 2)
    # Select number of simulations
    simulation_options = [1000, 10000, 100000]
    print("\nSelect number of simulations:")

    for i, option in enumerate(simulation_options, 1):
        print(f"{i}. {option:,} simulations")
    
    sim_choice = 0
    while sim_choice < 1 or sim_choice > len(simulation_options):
        try:
            sim_choice = int(input("\nEnter number for simulation count: "))
            if sim_choice < 1 or sim_choice > len(simulation_options):
                print(f"Please enter a number between 1 and {len(simulation_options)}")
        except ValueError:
            print("Please enter a valid number")
    
    num_simulations = simulation_options[sim_choice - 1]
    # Run the simulation
    print(f"\nRunning {num_simulations:,} simulations...")
    test_simulation(home_team, away_team, num_simulations, neutral_venue)


def main():
    """Main entry point for the CLI"""
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Load team data
        teams_data = load_team_data(args.data)
        
        # Create team manager
        team_manager = TeamManager()
        team_manager.load_teams(teams_data)
        
        # List teams and exit if --list-teams flag is used
        if args.list_teams:
            list_available_teams(team_manager, detailed=not args.brief)
            return
        
        # If team names are provided via arguments, run in command line mode
        if args.home and args.away:
            # First, list all teams for reference
            if not args.brief:
                list_available_teams(team_manager, detailed=True)
            
            home_team = team_manager.find_team(args.home, args.home_season)
            if not home_team:
                print(f"Error: Home team '{args.home}' for season '{args.home_season}' not found.")
                print("Use --list-teams to see available teams.")
                return
            
            away_team = team_manager.find_team(args.away, args.away_season)
            if not away_team:
                print(f"Error: Away team '{args.away}' for season '{args.away_season}' not found.")
                print("Use --list-teams to see available teams.")
                return
            
            # Display match details
            venue_type = "neutral venue" if args.neutral else "home/away format"
            print(f"\nSimulating: {home_team.get_display_name()} vs {away_team.get_display_name()} ({venue_type})")
            print(f"Running {args.simulations:,} simulations...\n")
            
            # Run simulation
            test_simulation(home_team, away_team, args.simulations, args.neutral)
        
        # Otherwise, start interactive mode
        else:
            interactive_mode(team_manager)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())