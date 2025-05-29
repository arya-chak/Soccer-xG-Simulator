"""
Match Simulator
Author: Arya Chakraborty

This file simulates matches between teams based on the data from the JSON file.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from soccer_xg_sim_dlp import Team, TeamManager

class Match:
    """
    Class to represent a soccer match between two teams and simulate outcomes
    based on Expected Goals (xG) statistics
    """

    def __init__(self, home_team: Team, away_team: Team, neutral_venue: bool = False):
        self.home_team = home_team
        self.away_team = away_team
        self.home_goals = 0
        self.away_goals = 0
        self.played = False
        self.neutral_venue = neutral_venue
        # Set default parameters for the simulation model
        self.home_advantage_factor = 1.0 if neutral_venue else 1.2  # Home teams tend to perform better
        self.variance_factor = 0.15       # Random variance to add realism

    def set_neutral_venue(self, is_neutral: bool = True) -> 'Match':
        """
        Set the match to be played at a neutral venue (no home advantage)
        Args:
            is_neutral: Whether the match is at a neutral venue (default: True)  
        Returns:
            The Match object itself (for method chaining)
        """

        self.neutral_venue = is_neutral
        self.home_advantage_factor = 1.0 if is_neutral else 1.2
        return self
    
    def simulate(self) -> 'Match':
        """
        Simulate a match between the two teams based on their xG statistics
        Returns:
            The Match object itself (for method chaining)
        """

        # ---- Calculate expected goals for HOME TEAM ----
        # 1. Start with the home team's base xG
        base_home_xg = self.home_team.avg_xg_for
        # 2. Apply home advantage factor (home teams create more chances)
        home_xg_with_advantage = base_home_xg * self.home_advantage_factor
        # 3. Apply the home team's attacking efficiency (how well they convert chances)
        home_xg_with_efficiency = home_xg_with_advantage * self.home_team.xg_efficiency
        # 4. Apply the away team's defensive efficiency (how well they prevent goals)
        # Note: Away teams have a disadvantage defensively, so we reduce their defensive efficiency
        away_defensive_factor = self.away_team.defensive_efficiency
        if not self.neutral_venue:
            away_defensive_factor *= (1 / self.home_advantage_factor)
        expected_home_goals = home_xg_with_efficiency / away_defensive_factor

        # ---- Calculate expected goals for AWAY TEAM ----
        # 1. Start with the away team's base xG
        base_away_xg = self.away_team.avg_xg_for
        # 2. Away teams have a disadvantage (inverse of home advantage)
        away_xg_with_disadvantage = base_away_xg
        if not self.neutral_venue:
            away_xg_with_disadvantage /= self.home_advantage_factor
        # 3. Apply the away team's attacking efficiency
        away_xg_with_efficiency = away_xg_with_disadvantage * self.away_team.xg_efficiency
        # 4. Apply the home team's defensive efficiency
        # Home teams get a defensive boost
        home_defensive_factor = self.home_team.defensive_efficiency
        if not self.neutral_venue:
            home_defensive_factor *= self.home_advantage_factor
        expected_away_goals = away_xg_with_efficiency / home_defensive_factor
        
        # Add random variation using Poisson distribution (common for soccer goals)
        self.home_goals = np.random.poisson(expected_home_goals)
        self.away_goals = np.random.poisson(expected_away_goals)
        self.played = True
        return self
    
    def get_result(self) -> Dict[str, Any]:
        """
        Get the match result
        Returns:
            Dictionary containing match result details
        """

        if not self.played:
            raise ValueError("Match has not been played yet. Call simulate() first.")
        
        return {
            'home_team': self.home_team.get_display_name(),
            'away_team': self.away_team.get_display_name(),
            'home_goals': self.home_goals,
            'away_goals': self.away_goals,
            'result': 'Home Win' if self.home_goals > self.away_goals else 
                    'Away Win' if self.away_goals > self.home_goals else 'Draw',
            'score_line': f"{self.home_goals}-{self.away_goals}"
        }

    def get_score_string(self) -> str:
        """
        Get a formatted score string
        Returns:
            String with the match score (e.g., "Team A 2-1 Team B")
        """

        if not self.played:
            return "Match not played yet"
        
        return f"{self.home_team.name} {self.home_goals} - {self.away_goals} {self.away_team.name}"
    
class MatchSimulator:
    """
    Class to run multiple simulations of matches between teams
    """

    def __init__(self):
        self.last_simulation_results = None

    def simulate_match(self, home_team: Team, away_team: Team, neutral_venue: bool = False) -> Dict[str, Any]:
        """
        Simulate a single match between two teams
        Args:
            home_team: The home team
            away_team: The away team
            neutral_venue: Whether the match is at a neutral venue   
        Returns:
            Dictionary with match result
        """

        match = Match(home_team, away_team, neutral_venue=neutral_venue)
        match.simulate()
        return match.get_result()
    
    def run_simulations(self, home_team: Team, away_team: Team, num_simulations: int = 10000, neutral_venue: bool = False) -> Dict[str, Any]:
        """
        Run multiple simulations of a match to estimate probabilities
        Args:
            home_team: The home team
            away_team: The away team
            num_simulations: Number of simulations to run (default: 10000)
            neutral_venue: Whether the match is at a neutral venue   
        Returns:
            Dictionary with simulation results and statistics
        """

        venue_type = "Neutral Venue" if neutral_venue else "Home/Away" 
        results = {
            'home_team': home_team.get_display_name(),
            'away_team': away_team.get_display_name(),
            'venue_type': venue_type,
            'num_simulations': num_simulations,
            'home_wins': 0,
            'away_wins': 0,
            'draws': 0,
            'home_goals': 0,
            'away_goals': 0,
            'score_counts': {},
            'home_goal_counts': {},
            'away_goal_counts': {}
        }

        # Run the simulations
        for _ in range(num_simulations):
            match = Match(home_team, away_team, neutral_venue=neutral_venue)
            match.simulate()
            match_result = match.get_result()
        
            # Update win/draw/loss counters
            if match_result['result'] == 'Home Win':
                results['home_wins'] += 1
            elif match_result['result'] == 'Away Win':
                results['away_wins'] += 1
            else:
                results['draws'] += 1
            
            # Update goal counts
            results['home_goals'] += match_result['home_goals']
            results['away_goals'] += match_result['away_goals']
            # Update score distribution
            score_key = match_result['score_line']
            results['score_counts'][score_key] = results['score_counts'].get(score_key, 0) + 1
            # Track distribution of goals
            home_goals = match_result['home_goals']
            away_goals = match_result['away_goals']
            results['home_goal_counts'][home_goals] = results['home_goal_counts'].get(home_goals, 0) + 1
            results['away_goal_counts'][away_goals] = results['away_goal_counts'].get(away_goals, 0) + 1

        # Calculate averages and probabilities
        results['avg_home_goals'] = results['home_goals'] / num_simulations
        results['avg_away_goals'] = results['away_goals'] / num_simulations
        results['home_win_prob'] = results['home_wins'] / num_simulations
        results['away_win_prob'] = results['away_wins'] / num_simulations
        results['draw_prob'] = results['draws'] / num_simulations
        # Find most common scores
        results['most_common_scores'] = sorted(
            [{'score': k, 'count': v, 'prob': v/num_simulations} 
             for k, v in results['score_counts'].items()],
            key=lambda x: x['count'], 
            reverse=True
        )[:10]  # Top 10 most common scores
        
        # Save last simulation results
        self.last_simulation_results = results
        return results
    
    def plot_simulation_results(self, results: Optional[Dict[str, Any]] = None) -> None:
        """
        Plot the results of the simulations
        Args:
            results: Simulation results dictionary (optional, uses last results if None)
        """

        if results is None:
            if self.last_simulation_results is None:
                raise ValueError("No simulation results available. Run simulations first.")
            results = self.last_simulation_results

        # Set up plot style
        sns.set(style="whitegrid")
        plt.figure(figsize=(15, 10))
        # Create subplots
        plt.subplot(2, 2, 1)
        # Plot match outcome probabilities
        labels = ['Home Win', 'Draw', 'Away Win']
        probabilities = [results['home_win_prob'], results['draw_prob'], results['away_win_prob']]
        colors = ['green', 'gray', 'red']
        plt.bar(labels, probabilities, color=colors)
        plt.title('Match Outcome Probabilities')
        plt.ylabel('Probability')
        plt.ylim(0, 1)

        for i, prob in enumerate(probabilities):
            plt.text(i, prob + 0.01, f'{prob:.1%}', ha='center')

        # Plot goal distribution for home team
        plt.subplot(2, 2, 2)
        # Convert goal counts dictionary to sorted lists
        max_goals = max(max(results['home_goal_counts'].keys()) if results['home_goal_counts'] else 0, max(results['away_goal_counts'].keys()) if results['away_goal_counts'] else 0)
        home_goals_distribution = [results['home_goal_counts'].get(i, 0) / results['num_simulations'] 
                                  for i in range(max_goals + 1)]
        away_goals_distribution = [results['away_goal_counts'].get(i, 0) / results['num_simulations'] 
                                  for i in range(max_goals + 1)]
        
        x = np.arange(max_goals + 1)
        plt.bar(x - 0.2, home_goals_distribution, width=0.4, label=results['home_team'].split(' (')[0], color='blue', alpha=0.7)
        plt.bar(x + 0.2, away_goals_distribution, width=0.4, label=results['away_team'].split(' (')[0], color='red', alpha=0.7)
        plt.title('Goal Distribution')
        plt.xlabel('Number of Goals')
        plt.ylabel('Probability')
        plt.xticks(x)
        plt.legend()
        # Plot most common scores
        plt.subplot(2, 2, 3)
        top_scores = results['most_common_scores'][:8]  # Limiting to top 8 for readability
        score_labels = [f"{score['score']}" for score in top_scores]
        score_probs = [score['prob'] for score in top_scores]
        plt.barh(score_labels, score_probs, color='purple', alpha=0.7)
        plt.title('Most Common Scores')
        plt.xlabel('Probability')
        plt.xlim(0, max(score_probs) * 1.1)

        for i, prob in enumerate(score_probs):
            plt.text(prob + 0.005, i, f'{prob:.1%}', va='center')

        # Add match summary text
        plt.subplot(2, 2, 4)
        plt.axis('off')
        home_team_name = results['home_team'].split(' (')[0]
        away_team_name = results['away_team'].split(' (')[0]
        summary_text = (
            f"Match Simulation Summary\n\n"
            f"{home_team_name} vs {away_team_name}\n\n"
            f"Based on {results['num_simulations']:,} simulations\n\n"
            f"Average Score: {home_team_name} {results['avg_home_goals']:.2f} - {results['avg_away_goals']:.2f} {away_team_name}\n\n"
            f"Win Probability:\n"
            f"{home_team_name}: {results['home_win_prob']:.1%}\n"
            f"Draw: {results['draw_prob']:.1%}\n"
            f"{away_team_name}: {results['away_win_prob']:.1%}\n\n"
            f"Most Likely Score: {top_scores[0]['score']} ({top_scores[0]['prob']:.1%})"
        )

        plt.text(0.5, 0.5, summary_text, ha='center', va='center', fontsize=12)
        plt.tight_layout()
        plt.show()

def calculate_expected_goals(team: Team, opponent: Team, is_home: bool = False, neutral_venue: bool = False) -> float:
    """
    Calculate expected goals for a team against a specific opponent
    Args:
        team: The attacking team
        opponent: The defending team
        is_home: Whether the attacking team is playing at home
        neutral_venue: Whether the match is at a neutral venue 
    Returns:
        Expected goals value
    """

    # 1. Base expected goals from team's xG
    base_xg = team.avg_xg_for
    # 2. Apply home/away factor (if not a neutral venue)
    if not neutral_venue:
        home_advantage = 1.2
        
        if is_home:
            # Home team gets an offensive boost
            base_xg *= home_advantage
        else:
            # Away team gets an offensive penalty
            base_xg /= home_advantage
    
    # 3. Apply team's efficiency at converting chances
    xg_with_efficiency = base_xg * team.xg_efficiency
    # 4. Apply opponent's defensive efficiency
    # Adjust defensive efficiency based on home/away (if not a neutral venue)
    opponent_defensive_factor = opponent.defensive_efficiency
    if not neutral_venue:
        home_advantage = 1.2
        
        if is_home:
            # When team is at home, the away opponent has reduced defensive efficiency
            opponent_defensive_factor /= home_advantage
        else:
            # When team is away, the home opponent has increased defensive efficiency
            opponent_defensive_factor *= home_advantage
    
    # Final expected goals calculation
    expected_goals = xg_with_efficiency / opponent_defensive_factor
    return expected_goals

def predict_score_probability(home_team: Team, away_team: Team, home_goals: int, away_goals: int, neutral_venue: bool = False) -> float:
    """
    Calculate the probability of a specific score occurring
    Args:
        home_team: The home team
        away_team: The away team
        home_goals: Number of goals for home team
        away_goals: Number of goals for away team
        neutral_venue: Whether the match is at a neutral venue   
    Returns:
        Probability of the specified score occurring
    """

    # Calculate expected goals
    home_xg = calculate_expected_goals(home_team, away_team, is_home=True, neutral_venue=neutral_venue)
    away_xg = calculate_expected_goals(away_team, home_team, is_home=False, neutral_venue=neutral_venue)
    # Calculate probability using Poisson distribution
    home_prob = stats.poisson.pmf(home_goals, home_xg)
    away_prob = stats.poisson.pmf(away_goals, away_xg)
    # Combined probability (assuming independence)
    score_prob = home_prob * away_prob
    return score_prob

def test_simulation(home_team: Team, away_team: Team, num_simulations: int = 10000, neutral_venue: bool = False) -> None:
    """
    Run a test simulation between two teams and display the results
    Args:
        home_team: The home team
        away_team: The away team
        num_simulations: Number of simulations to run
        neutral_venue: Whether the match is at a neutral venue
    """

    venue_text = "at a neutral venue" if neutral_venue else "with home advantage"
    print(f"Simulating: {home_team.get_display_name()} vs {away_team.get_display_name()} {venue_text}")
    print(f"Running {num_simulations} simulations...\n")
    simulator = MatchSimulator()
    results = simulator.run_simulations(home_team, away_team, num_simulations, neutral_venue=neutral_venue)
    print(f"Expected Score: {home_team.name} {results['avg_home_goals']:.2f} - {results['avg_away_goals']:.2f} {away_team.name}")
    print(f"Win Probability: {home_team.name}: {results['home_win_prob']:.2%}, Draw: {results['draw_prob']:.2%}, {away_team.name}: {results['away_win_prob']:.2%}")
    print("\nMost Common Scores:")
    
    for i, score in enumerate(results['most_common_scores'][:5]):
        print(f"  {i+1}. {score['score']}: {score['prob']:.2%}")
    
    # Calculate theoretical probability of the most common score
    most_common = results['most_common_scores'][0]['score']
    home_goals, away_goals = map(int, most_common.split('-'))
    theoretical_prob = predict_score_probability(home_team, away_team, home_goals, away_goals, neutral_venue)
    print(f"\nTheoretical probability of {most_common}: {theoretical_prob:.2%}")
    # Plot the results
    simulator.plot_simulation_results(results)

if __name__ == "__main__":
    # Example of how to use this module with your existing data loading module
    # 1. First, load teams from your data file using your existing module
    from soccer_xg_sim_dlp import load_team_data, TeamManager
    
    try:
        # 2. Load the team data
        # Replace 'teams_data.json' with your actual file path
        teams_data = load_team_data('teams_data.json')
        # 3. Create a team manager and load the teams
        team_manager = TeamManager()
        team_manager.load_teams(teams_data)
        # 4. Find specific teams for simulation
        man_utd = team_manager.find_team("Manchester United", "2024-2025")
        real_madrid = team_manager.find_team("Real Madrid", "2021-2022")
        
        if man_utd and real_madrid:
            # 5. Run test simulation with home advantage
            print("\n=== SIMULATION WITH HOME ADVANTAGE ===")
            test_simulation(man_utd, real_madrid, 10000, neutral_venue=False)
            # 6. Run test simulation at neutral venue
            print("\n=== SIMULATION AT NEUTRAL VENUE ===")
            test_simulation(man_utd, real_madrid, 10000, neutral_venue=True)
            # 7. Compare the results
            print("\nComparing simulations shows the impact of home advantage on match outcomes")
        else:
            print("Teams not found. Check team names and seasons.")
            
    except Exception as e:
        print(f"Error running example: {e}")
