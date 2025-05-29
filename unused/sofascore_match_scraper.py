"""
sofascore_match_scraper.py
Author: Arya Chakraborty

This script focuses on extracting match data and xG statistics from SofaScore.
"""

import os
import json
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

class SofaScoreMatchScraper:
    """Class to scrape match data from SofaScore with a focus on xG statistics."""
    
    def __init__(self, cache_dir='data', headless=False):
        """Initialize the scraper."""
        self.cache_dir = cache_dir
        self.headless = headless
        self.driver = None
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Team ID mapping
        self.team_ids = {
            'manchester city': 17,
            'manchester united': 35,
            'liverpool': 44,
            'arsenal': 42,
            'chelsea': 38,
            'tottenham': 33,
            # Add more as needed
        }
        
        # Initialize the driver
        self._initialize_driver()
    
    def _initialize_driver(self):
        """Initialize and return a Selenium WebDriver instance."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        return self.driver
    
    def _random_delay(self, min_seconds=1, max_seconds=3):
        """Add a random delay to avoid detection."""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _get_cached_data(self, filename):
        """Get data from cache if it exists."""
        cache_file = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cached data: {e}")
        
        return None
    
    def _cache_data(self, filename, data):
        """Cache data to a file."""
        cache_file = os.path.join(self.cache_dir, filename)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved data to {cache_file}")
        except Exception as e:
            print(f"Error caching data: {e}")
    
    def get_team_id(self, team_name):
        """Get the SofaScore ID for a team."""
        return self.team_ids.get(team_name.lower())
    
    def get_team_matches(self, team_name, season="2022-2023", force_refresh=False):
        """
        Get matches for a specific team and season.
        
        Args:
            team_name (str): Name of the team (e.g., "Manchester City")
            season (str): Season in format YYYY-YYYY (e.g., "2022-2023")
            force_refresh (bool): If True, ignore cache and fetch fresh data
            
        Returns:
            dict: Dictionary with team match data
        """
        team_id = self.get_team_id(team_name.lower())
        if not team_id:
            print(f"Team ID not found for {team_name}")
            return None
        
        # Check cache first
        cache_filename = f"{team_name.lower().replace(' ', '_')}_{season}_matches.json"
        if not force_refresh:
            cached_data = self._get_cached_data(cache_filename)
            if cached_data:
                print(f"Using cached match data for {team_name} ({season})")
                return cached_data
        
        print(f"Fetching matches for {team_name} ({season})...")
        
        # Initialize match data
        team_data = {
            'team_name': team_name,
            'team_id': team_id,
            'season': season,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'matches': []
        }
        
        try:
            # Access team page
            self.driver.get(f"https://www.sofascore.com/team/football/{team_name.replace(' ', '-').lower()}/{team_id}")
            self._random_delay(3, 5)
            
            # Accept cookies if prompted
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'OK') or contains(text(), 'cookie')]"))
                )
                cookie_button.click()
                self._random_delay(1, 2)
            except:
                print("No cookie popup or already accepted")
            
            # Find and click on the "Fixtures" or "Results" tab
            try:
                tabs = self.driver.find_elements(By.XPATH, "//div[contains(@role, 'tab') or contains(@class, 'tab')]")
                fixtures_tab = None
                
                for tab in tabs:
                    if tab.text and ('FIXTURES' in tab.text.upper() or 'RESULTS' in tab.text.upper() or 'MATCHES' in tab.text.upper()):
                        fixtures_tab = tab
                        break
                
                if fixtures_tab:
                    print(f"Found tab: {fixtures_tab.text}")
                    fixtures_tab.click()
                    self._random_delay(2, 3)
                else:
                    print("Fixtures/Results tab not found, trying to find match elements directly")
            except Exception as e:
                print(f"Error clicking fixtures tab: {e}")
            
            # Now let's try to find match elements
            # First, take a screenshot to see the current state
            self.driver.save_screenshot(f"{team_name.lower().replace(' ', '_')}_matches_page.png")
            
            # Try multiple selectors for match elements
            match_selectors = [
                "//div[contains(@class, 'event') or contains(@class, 'match')]",
                "//div[contains(@class, 'cell')]//a[contains(@href, '/event/')]",
                "//div[contains(@class, 'event-list')]//div",
                "//table//tr[contains(@class, 'event')]",
                "//a[contains(@href, '/event/')]"
            ]
            
            match_elements = []
            
            for selector in match_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"Found {len(elements)} potential match elements with selector: {selector}")
                    match_elements = elements
                    break
            
            if not match_elements:
                print("No match elements found with any selector")
                # Save the page source for debugging
                with open(f"{team_name.lower().replace(' ', '_')}_page_source.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print(f"Saved page source to {team_name.lower().replace(' ', '_')}_page_source.html")
                
                # As a fallback, try to scrape any useful match information from the page
                try:
                    # Look for any match-like information
                    match_info = self.driver.find_elements(By.XPATH, 
                        "//div[contains(text(), 'vs') or contains(text(), '-')]//ancestor::div[contains(@class, 'sc-')]")
                    
                    if match_info:
                        print(f"Found {len(match_info)} potential match info elements as fallback")
                        for i, info in enumerate(match_info[:5]):  # First 5 only
                            print(f"Match info {i+1}: {info.text[:100]}...")
                except Exception as e:
                    print(f"Error finding fallback match info: {e}")
            
            # Process match elements (if found)
            for i, match_element in enumerate(match_elements[:20]):  # Limit to first 20 matches for testing
                try:
                    # Extract basic match information
                    match_text = match_element.text
                    print(f"Processing match {i+1}: {match_text[:50]}...")
                    
                    # Try to get match URL (for later detailed scraping)
                    match_url = None
                    try:
                        if match_element.tag_name == 'a':
                            match_url = match_element.get_attribute('href')
                        else:
                            link = match_element.find_element(By.XPATH, ".//a[contains(@href, '/event/')]")
                            match_url = link.get_attribute('href')
                    except:
                        # If we can't find a direct link, look for an event ID and construct URL
                        try:
                            event_id = match_element.get_attribute('data-event-id') or match_element.get_attribute('id')
                            if event_id and event_id.isdigit():
                                match_url = f"https://www.sofascore.com/event/{event_id}"
                        except:
                            pass
                    
                    # Parse match information from text (adjust based on actual format)
                    # This is simplified and would need to be adapted to actual data format
                    match_data = {
                        'match_text': match_text,
                        'match_url': match_url,
                        'has_details': False  # We'll set this to True after scraping details
                    }
                    
                    # Only add matches with some useful data
                    if match_data['match_text'] or match_data['match_url']:
                        team_data['matches'].append(match_data)
                    
                except Exception as e:
                    print(f"Error processing match {i+1}: {e}")
            
            print(f"Processed {len(team_data['matches'])} matches")
            
            # Cache the basic match data
            self._cache_data(cache_filename, team_data)
            
            return team_data
            
        except Exception as e:
            print(f"Error fetching matches: {e}")
            return None
    
    def get_match_details(self, match_url):
        """
        Get detailed statistics for a specific match including xG.
        
        Args:
            match_url (str): URL of the match detail page
            
        Returns:
            dict: Match statistics including xG if available
        """
        if not match_url:
            return None
        
        # Extract match ID from URL for caching
        match_id = match_url.split('/')[-1]
        cache_filename = f"match_{match_id}_details.json"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_filename)
        if cached_data:
            print(f"Using cached data for match {match_id}")
            return cached_data
        
        print(f"Fetching details for match {match_id}...")
        
        try:
            # Navigate to match page
            self.driver.get(match_url)
            self._random_delay(3, 5)
            
            # Take screenshot for debugging
            self.driver.save_screenshot(f"match_{match_id}_page.png")
            
            # Initialize match details
            match_details = {
                'match_id': match_id,
                'match_url': match_url,
                'home_team': '',
                'away_team': '',
                'score': '',
                'date': '',
                'competition': '',
                'statistics': {},
                'has_xg': False,
                'home_xg': None,
                'away_xg': None
            }
            
            # Extract basic match information
            try:
                # Team names
                team_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'team-name')]")
                if len(team_elements) >= 2:
                    match_details['home_team'] = team_elements[0].text
                    match_details['away_team'] = team_elements[1].text
                
                # Score
                score_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'score')]")
                match_details['score'] = score_element.text
                
                # Date
                date_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'date')]")
                match_details['date'] = date_element.text
                
                # Competition
                competition_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'competition')]")
                match_details['competition'] = competition_element.text
                
            except Exception as e:
                print(f"Error extracting basic match info: {e}")
            
            # Look for statistics tab and click it
            try:
                stats_tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Statistics') or contains(text(), 'Stats')]"))
                )
                stats_tab.click()
                self._random_delay(2, 3)
                
                # Now look for xG statistics
                xg_elements = self.driver.find_elements(By.XPATH, 
                    "//div[contains(text(), 'Expected goals') or contains(text(), 'xG')]//ancestor::div[contains(@class, 'sc-')]")
                
                if xg_elements:
                    match_details['has_xg'] = True
                    
                    # Extract xG values - this is simplified and would need adaptation
                    stats_row = xg_elements[0]
                    values = stats_row.find_elements(By.XPATH, ".//div[contains(@class, 'value')]")
                    
                    if len(values) >= 2:
                        try:
                            match_details['home_xg'] = float(values[0].text)
                            match_details['away_xg'] = float(values[1].text)
                        except:
                            # If we can't convert to float, just store the text
                            match_details['home_xg'] = values[0].text
                            match_details['away_xg'] = values[1].text
                
                # Get other statistics
                stat_rows = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'stat-row')]")
                for row in stat_rows:
                    try:
                        stat_name = row.find_element(By.XPATH, ".//div[contains(@class, 'stat-name')]").text
                        home_value = row.find_element(By.XPATH, ".//div[contains(@class, 'home-value')]").text
                        away_value = row.find_element(By.XPATH, ".//div[contains(@class, 'away-value')]").text
                        
                        match_details['statistics'][stat_name] = {
                            'home': home_value,
                            'away': away_value
                        }
                    except:
                        continue
                
            except Exception as e:
                print(f"Error extracting statistics: {e}")
                # Save page source for debugging
                with open(f"match_{match_id}_source.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
            
            # Cache the match details
            self._cache_data(cache_filename, match_details)
            
            return match_details
            
        except Exception as e:
            print(f"Error fetching match details: {e}")
            return None
    
    def get_team_season_data(self, team_name, season="2022-2023", force_refresh=False):
        """
        Get comprehensive season data for a team including match details with xG.
        
        Args:
            team_name (str): Name of the team
            season (str): Season identifier
            force_refresh (bool): Whether to ignore cache
            
        Returns:
            dict: Complete team season data with match details
        """
        # First get the basic match list
        matches_data = self.get_team_matches(team_name, season, force_refresh)
        
        if not matches_data:
            return None
        
        # Check if we already have complete data with details
        cache_filename = f"{team_name.lower().replace(' ', '_')}_{season}_complete.json"
        if not force_refresh:
            cached_data = self._get_cached_data(cache_filename)
            if cached_data:
                print(f"Using cached complete data for {team_name} ({season})")
                return cached_data
        
        # Create a copy to avoid modifying the original
        complete_data = matches_data.copy()
        complete_data['matches_with_details'] = []
        
        # Get details for each match that has a URL
        for i, match in enumerate(matches_data['matches']):
            if match.get('match_url'):
                print(f"Getting details for match {i+1}/{len(matches_data['matches'])}...")
                match_details = self.get_match_details(match['match_url'])
                
                if match_details:
                    complete_data['matches_with_details'].append(match_details)
                
                # Add a delay between requests
                self._random_delay(2, 4)
        
        # Calculate some aggregate statistics
        if complete_data['matches_with_details']:
            xg_matches = [m for m in complete_data['matches_with_details'] if m.get('has_xg')]
            
            if xg_matches:
                complete_data['xg_stats'] = {
                    'matches_with_xg': len(xg_matches),
                    'total_matches': len(complete_data['matches_with_details']),
                    'avg_xg_for': sum(float(m['home_xg']) if isinstance(m['home_xg'], (int, float)) else 0 
                                       for m in xg_matches) / len(xg_matches),
                    'avg_xg_against': sum(float(m['away_xg']) if isinstance(m['away_xg'], (int, float)) else 0 
                                           for m in xg_matches) / len(xg_matches)
                }
        
        # Cache the complete data
        self._cache_data(cache_filename, complete_data)
        
        return complete_data
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None

# Test the scraper
if __name__ == "__main__":
    scraper = SofaScoreMatchScraper()
    
    try:
        # Test with Manchester City for 2022-2023 season
        team_name = "Manchester City"
        season = "2022-2023"
        
        print(f"Testing match scraper with {team_name} for {season} season...")
        
        # Get basic match list
        matches = scraper.get_team_matches(team_name, season)
        
        if matches and matches['matches']:
            print(f"Found {len(matches['matches'])} matches")
            
            # Test match details for first match with URL
            for match in matches['matches']:
                if match.get('match_url'):
                    print(f"\nTesting match details for: {match['match_text'][:50]}...")
                    details = scraper.get_match_details(match['match_url'])
                    
                    if details:
                        print(f"Match details: {details['home_team']} vs {details['away_team']}")
                        print(f"Score: {details['score']}")
                        print(f"Has xG data: {details['has_xg']}")
                        if details['has_xg']:
                            print(f"xG: {details['home_xg']} - {details['away_xg']}")
                    
                    # Just test one match for now
                    break
        else:
            print("No matches found")
    
    finally:
        # Close the browser
        scraper.close()