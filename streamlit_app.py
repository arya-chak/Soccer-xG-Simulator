"""
Soccer xG Simulator Streamlit App
Author: Arya Chakraborty

This is the Streamlit app for the Soccer xG Simulator project so users can interact through a web interface.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="Soccer xG Match Simulator",
    page_icon="⚽",
    layout="wide"
)

# Main title
st.title("⚽ Soccer xG Match Simulator")
st.write("Predict soccer match outcomes using Expected Goals (xG) statistics")

# Load team data
@st.cache_data
def load_teams():
    """Load team data with caching for better performance"""
    try:
        from soccer_xg_sim_dlp import load_team_data, TeamManager
        
        # Load the data
        teams_data = load_team_data('teams_data.json')
        team_manager = TeamManager()
        team_manager.load_teams(teams_data)
        
        return team_manager
    except Exception as e:
        st.error(f"Error loading team data: {e}")
        return None

# Load the teams
team_manager = load_teams()

if team_manager:
    teams = team_manager.get_all_teams()
    
    # Create team selection interface
    st.subheader("Select Teams for Simulation")
    
    # Create two columns for team selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Home Team**")
        # Create list of team options for dropdown
        team_options = [f"{team.name} ({team.season})" for team in teams]
        home_selection = st.selectbox(
            "Choose Home Team:",
            team_options,
            index=0
        )
        
        # Find the selected home team object
        home_team_name, home_season = home_selection.split(" (")
        home_season = home_season.rstrip(")")
        home_team = team_manager.find_team(home_team_name, home_season)
        
        if home_team:
            st.write(f"🏠 **Name:** {home_team.name}")
            st.write(f"📅 **Season:** {home_team.season}")
            st.write(f"🏆 **League:** {getattr(home_team, 'league', 'N/A')}")
            st.write(f"👨‍💼 **Coach:** {getattr(home_team, 'coach', 'N/A')}")
            
            # Notable players
            notable_players = getattr(home_team, 'notable_players', [])
            if notable_players:
                st.write(f"⭐ **Notable Players:** {', '.join(notable_players)}")
            else:
                st.write(f"⭐ **Notable Players:** N/A")
            
            # Notes
            notes = getattr(home_team, 'notes', '')
            if notes:
                st.write(f"📝 **Notes:** {notes}")
            else:
                st.write(f"📝 **Notes:** N/A")
    
    with col2:
        st.write("**Away Team**")
        away_selection = st.selectbox(
            "Choose Away Team:",
            team_options,
            index=1 if len(team_options) > 1 else 0
        )
        
        # Find the selected away team object
        away_team_name, away_season = away_selection.split(" (")
        away_season = away_season.rstrip(")")
        away_team = team_manager.find_team(away_team_name, away_season)
        
        if away_team:
            st.write(f"✈️ **Name:** {away_team.name}")
            st.write(f"📅 **Season:** {away_team.season}")
            st.write(f"🏆 **League:** {getattr(away_team, 'league', 'N/A')}")
            st.write(f"👨‍💼 **Coach:** {getattr(away_team, 'coach', 'N/A')}")
            
            # Notable players
            notable_players = getattr(away_team, 'notable_players', [])
            if notable_players:
                st.write(f"⭐ **Notable Players:** {', '.join(notable_players)}")
            else:
                st.write(f"⭐ **Notable Players:** N/A")
            
            # Notes
            notes = getattr(away_team, 'notes', '')
            if notes:
                st.write(f"📝 **Notes:** {notes}")
            else:
                st.write(f"📝 **Notes:** N/A")
    
    # Show selected matchup
    if home_team and away_team:
        st.write("---")
        st.subheader("Selected Matchup")
        st.write(f"🏠 **{home_team.name}** ({home_team.season}) vs ✈️ **{away_team.name}** ({away_team.season})")
        
        if home_team.name == away_team.name and home_team.season == away_team.season:
            st.warning("⚠️ You've selected the same team for both home and away!")
        
        # Simulation Controls
        st.write("---")
        st.subheader("Simulation Settings")
        
        # Create two columns for simulation controls
        settings_col1, settings_col2 = st.columns(2)
        
        with settings_col1:
            # Venue selection
            venue_type = st.radio(
                "Select Venue Type:",
                ["Home/Away (with home advantage)", "Neutral Venue (no advantage)"],
                index=0
            )
            neutral_venue = (venue_type == "Neutral Venue (no advantage)")
            
        with settings_col2:
            # Number of simulations
            num_simulations = st.selectbox(
                "Number of Simulations:",
                [1000, 5000, 10000, 25000, 50000],
                index=2  # Default to 10000
            )
        
        # Run simulation button
        st.write("---")
        if st.button("🚀 Run Match Simulation", type="primary", use_container_width=True):
            venue_text = "neutral venue" if neutral_venue else "home advantage"
            
            with st.spinner(f"Running {num_simulations:,} simulations..."):
                try:
                    # Import and run the simulator
                    from xg_simulator import MatchSimulator
                    
                    simulator = MatchSimulator()
                    results = simulator.run_simulations(
                        home_team, 
                        away_team, 
                        num_simulations, 
                        neutral_venue=neutral_venue
                    )
                    
                    # Display Results
                    st.success("✅ Simulation Complete!")
                    
                    # Main Results Header
                    st.subheader("Match Prediction Results")
                    venue_display = "Neutral Venue" if neutral_venue else "Home/Away"
                    st.write(f"**Venue:** {venue_display} | **Simulations:** {num_simulations:,}")
                    
                    # Expected Score - Make it prominent
                    st.write("### 📊 Expected Score")
                    score_col1, score_col2, score_col3 = st.columns([2, 1, 2])
                    with score_col1:
                        st.write(f"**{home_team.name}**")
                        st.write(f"**{results['avg_home_goals']:.2f}**")
                    with score_col2:
                        st.write("**VS**")
                        st.write("**-**")
                    with score_col3:
                        st.write(f"**{away_team.name}**")
                        st.write(f"**{results['avg_away_goals']:.2f}**")
                    
                    # Win Probabilities with more detail
                    st.write("### 🏆 Match Outcome Probabilities")
                    prob_col1, prob_col2, prob_col3 = st.columns(3)
                    
                    with prob_col1:
                        st.metric(
                            f"🏠 {home_team.name} Win", 
                            f"{results['home_win_prob']:.1%}",
                            f"{results['home_wins']:,} out of {num_simulations:,}"
                        )
                    
                    with prob_col2:
                        st.metric(
                            "🤝 Draw", 
                            f"{results['draw_prob']:.1%}",
                            f"{results['draws']:,} out of {num_simulations:,}"
                        )
                    
                    with prob_col3:
                        st.metric(
                            f"✈️ {away_team.name} Win", 
                            f"{results['away_win_prob']:.1%}",
                            f"{results['away_wins']:,} out of {num_simulations:,}"
                        )
                    
                    # Detailed Statistics
                    st.write("### 📈 Detailed Statistics")
                    
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.write("**Goal Statistics:**")
                        st.write(f"• Total goals simulated: {results['home_goals'] + results['away_goals']:,}")
                        st.write(f"• {home_team.name} total goals: {results['home_goals']:,}")
                        st.write(f"• {away_team.name} total goals: {results['away_goals']:,}")
                        st.write(f"• Average goals per match: {(results['home_goals'] + results['away_goals'])/num_simulations:.2f}")
                    
                    with detail_col2:
                        st.write("**Match Statistics:**")
                        high_scoring = sum(1 for score in results['score_counts'].keys() 
                                         if sum(map(int, score.split('-'))) >= 4)
                        low_scoring = sum(1 for score in results['score_counts'].keys() 
                                        if sum(map(int, score.split('-'))) <= 1)
                        st.write(f"• High-scoring matches (4+ goals): {high_scoring/num_simulations:.1%}")
                        st.write(f"• Low-scoring matches (≤1 goal): {low_scoring/num_simulations:.1%}")
                        st.write(f"• Most common total goals: {max(results['score_counts'].keys(), key=lambda x: sum(map(int, x.split('-'))))}")
                    
                    # Most Common Scores - Enhanced
                    st.write("### 🎯 Most Likely Scorelines")
                    
                    # Create two columns for better layout
                    scores_col1, scores_col2 = st.columns(2)
                    
                    top_10_scores = results['most_common_scores'][:10]
                    mid_point = len(top_10_scores) // 2
                    
                    with scores_col1:
                        st.write("**Top 5 Most Likely:**")
                        for i, score in enumerate(top_10_scores[:5]):
                            st.write(f"{i+1}. **{score['score']}** - {score['prob']:.1%} ({score['count']:,} times)")
                    
                    with scores_col2:
                        if len(top_10_scores) > 5:
                            st.write("**Next 5 Most Likely:**")
                            for i, score in enumerate(top_10_scores[5:10], 6):
                                st.write(f"{i}. **{score['score']}** - {score['prob']:.1%} ({score['count']:,} times)")
                    
                    # Probability Insights
                    st.write("### 🧠 Key Insights")
                    insights_col1, insights_col2 = st.columns(2)
                    
                    with insights_col1:
                        st.write("**Attacking Analysis:**")
                        home_shutout = results['away_goal_counts'].get(0, 0) / num_simulations
                        away_shutout = results['home_goal_counts'].get(0, 0) / num_simulations
                        st.write(f"• {home_team.name} clean sheet: {home_shutout:.1%}")
                        st.write(f"• {away_team.name} clean sheet: {away_shutout:.1%}")
                        
                        home_2plus = sum(count for goals, count in results['home_goal_counts'].items() if goals >= 2)
                        away_2plus = sum(count for goals, count in results['away_goal_counts'].items() if goals >= 2)
                        st.write(f"• {home_team.name} scores 2+: {home_2plus/num_simulations:.1%}")
                        st.write(f"• {away_team.name} scores 2+: {away_2plus/num_simulations:.1%}")
                    
                    with insights_col2:
                        st.write("**Match Dynamics:**")
                        both_score = sum(count for score, count in results['score_counts'].items() 
                                       if all(int(g) > 0 for g in score.split('-')))
                        st.write(f"• Both teams score: {both_score/num_simulations:.1%}")
                        
                        over_2_5 = sum(count for score, count in results['score_counts'].items() 
                                     if sum(int(g) for g in score.split('-')) > 2.5)
                        st.write(f"• Over 2.5 goals: {over_2_5/num_simulations:.1%}")
                        
                        home_advantage_effect = results['home_win_prob'] - results['away_win_prob']
                        if not neutral_venue:
                            st.write(f"• Home advantage effect: +{home_advantage_effect:.1%}")
                        else:
                            st.write("• No home advantage (neutral venue)")

                    # Interactive Visualizations
                    st.write("### 📊 Interactive Visualizations")
                    
                    # Create tabs for different charts
                    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Win Probabilities", "Goal Distribution", "Score Frequencies"])
                    
                    with chart_tab1:
                        # Win Probability Pie Chart
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=[f'{home_team.name} Win', 'Draw', f'{away_team.name} Win'],
                            values=[results['home_win_prob'], results['draw_prob'], results['away_win_prob']],
                            hole=0.3,
                            marker_colors=['#2E8B57', '#808080', '#DC143C']
                        )])
                        fig_pie.update_layout(
                            title=f"Match Outcome Probabilities ({num_simulations:,} simulations)",
                            height=400
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with chart_tab2:
                        # Goal Distribution Bar Chart
                        max_goals = max(max(results['home_goal_counts'].keys()) if results['home_goal_counts'] else 0,
                                       max(results['away_goal_counts'].keys()) if results['away_goal_counts'] else 0)
                        
                        goals_range = list(range(max_goals + 1))
                        home_probs = [results['home_goal_counts'].get(i, 0) / num_simulations for i in goals_range]
                        away_probs = [results['away_goal_counts'].get(i, 0) / num_simulations for i in goals_range]
                        
                        fig_goals = go.Figure()
                        fig_goals.add_trace(go.Bar(
                            name=home_team.name,
                            x=goals_range,
                            y=home_probs,
                            marker_color='#2E8B57',
                            opacity=0.7
                        ))
                        fig_goals.add_trace(go.Bar(
                            name=away_team.name,
                            x=goals_range,
                            y=away_probs,
                            marker_color='#DC143C',
                            opacity=0.7
                        ))
                        
                        fig_goals.update_layout(
                            title='Goal Distribution by Team',
                            xaxis_title='Number of Goals',
                            yaxis_title='Probability',
                            barmode='group',
                            height=400
                        )
                        st.plotly_chart(fig_goals, use_container_width=True)
                    
                    with chart_tab3:
                        # Most Common Scores Horizontal Bar Chart
                        top_scores = results['most_common_scores'][:8]  # Top 8 scores
                        score_labels = [score['score'] for score in top_scores]
                        score_probs = [score['prob'] for score in top_scores]
                        
                        fig_scores = go.Figure(go.Bar(
                            x=score_probs,
                            y=score_labels,
                            orientation='h',
                            marker_color='#4169E1',
                            text=[f"{prob:.1%}" for prob in score_probs],
                            textposition='auto'
                        ))
                        
                        fig_scores.update_layout(
                            title='Most Common Scorelines',
                            xaxis_title='Probability',
                            yaxis_title='Score',
                            height=400,
                            yaxis={'categoryorder': 'total ascending'}
                        )
                        st.plotly_chart(fig_scores, use_container_width=True)
                    
                    # Additional Summary Chart - Win Probability vs Expected Goals
                    st.write("### 🎯 Match Summary Visualization")
                    
                    summary_col1, summary_col2 = st.columns(2)
                    
                    with summary_col1:
                        # Expected Goals Comparison
                        fig_xg = go.Figure()
                        
                        teams = [home_team.name, away_team.name]
                        expected_goals = [results['avg_home_goals'], results['avg_away_goals']]
                        
                        fig_xg.add_trace(go.Bar(
                            x=teams,
                            y=expected_goals,
                            marker_color=['#2E8B57', '#DC143C'],
                            text=[f"{xg:.2f}" for xg in expected_goals],
                            textposition='auto'
                        ))
                        
                        fig_xg.update_layout(
                            title='Expected Goals Comparison',
                            yaxis_title='Expected Goals',
                            height=300
                        )
                        st.plotly_chart(fig_xg, use_container_width=True)
                    
                    with summary_col2:
                        # Win Probability Bar Chart
                        fig_win_prob = go.Figure()
                        
                        outcomes = [f'{home_team.name}\nWin', 'Draw', f'{away_team.name}\nWin']
                        probabilities = [results['home_win_prob'], results['draw_prob'], results['away_win_prob']]
                        
                        fig_win_prob.add_trace(go.Bar(
                            x=outcomes,
                            y=probabilities,
                            marker_color=['#2E8B57', '#808080', '#DC143C'],
                            text=[f"{prob:.1%}" for prob in probabilities],
                            textposition='auto'
                        ))
                        
                        fig_win_prob.update_layout(
                            title='Win Probabilities',
                            yaxis_title='Probability',
                            height=300
                        )
                        st.plotly_chart(fig_win_prob, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error running simulation: {e}")

else:
    st.error("❌ Could not load team data. Check that teams_data.json exists.")