"""
SofaScore Direct Fixtures Scraper
Author: Arya Chakraborty

This script targets SofaScore's fixtures pages directly for better results.
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
from webdriver_manager.chrome import ChromeDriverManager

class SofaScoreDirectScraper:
    """Class to scrape soccer match data from SofaScore using direct fixtures URLs."""
    
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
        
        # League ID mapping (for 2022-2023 season)
        self.league_ids = {
            'premier league': 17,
            'la liga': 8,
            'bundesliga': 35,
            'serie a': 23,
            'ligue 1': 34
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
    
    def get_league_fixtures(self, league_name, season_year="2022-2023", force_refresh=False):
        """
        Get all fixtures for a specific league and season.
        
        Args:
            league_name (str): Name of the league (e.g., "Premier League")
            season_year (str): Season in format YYYY-YYYY (e.g., "2022-2023")
            force_refresh (bool): If True, ignore cache and fetch fresh data
            
        Returns:
            dict: Dictionary with league fixtures
        """
        # Normalize league name
        league_name_lower = league_name.lower()
        
        # Get league ID
        league_id = self.league_ids.get(league_name_lower)
        if not league_id:
            print(f"League ID not found for {league_name}")
            return None
        
        # Check cache first
        cache_filename = f"{league_name_lower.replace(' ', '_')}_{season_year}_fixtures.json"
        if not force_refresh:
            cached_data = self._get_cached_data(cache_filename)
            if cached_data:
                print(f"Using cached fixture data for {league_name} ({season_year})")
                return cached_data
        
        # Extract season number from year
        # For 2022-2023, we need 2022 part for the URL
        season_number = season_year.split('-')[0]
        
        # Initialize league data
        league_data = {
            'league_name': league_name,
            'league_id': league_id,
            'season': season_year,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'fixtures': []
        }
        
        try:
            # Access league fixtures directly
            # This URL pattern is for league fixtures
            fixtures_url = f"https://www.sofascore.com/tournament/football/{league_name.replace(' ', '-').lower()}/{league_id}/season/{season_number}"
            print(f"Accessing league fixtures at: {fixtures_url}")
            
            self.driver.get(fixtures_url)
            self._random_delay(5, 7)  # Longer delay for initial page load
            
            # Take a screenshot to see what we're working with
            self.driver.save_screenshot(f"{league_name_lower.replace(' ', '_')}_fixtures_page.png")
            
            # Check if we have fixtures tab or need to navigate to it
            try:
                fixtures_tab = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Fixtures') or contains(text(), 'Schedule')]")
                fixtures_tab.click()
                self._random_delay(3, 5)
                print("Clicked on Fixtures tab")
            except:
                print("No fixtures tab found or already on fixtures page")
            
            # Find matches/fixtures on the page
            # Take another screenshot after any navigation
            self.driver.save_screenshot(f"{league_name_lower.replace(' ', '_')}_fixtures_tab.png")
            
            # Try different selectors for match elements
            match_element_selectors = [
                "//div[contains(@class, 'event')]",
                "//a[contains(@href, '/event/')]",
                "//div[contains(@class, 'rows')]//div[contains(@class, 'row')]",
                "//div[contains(@class, 'match')]"
            ]
            
            for selector in match_element_selectors:
                match_elements = self.driver.find_elements(By.XPATH, selector)
                if match_elements:
                    print(f"Found {len(match_elements)} potential fixture elements with selector: {selector}")
                    break
            else:
                match_elements = []
                print("No fixture elements found with any selector")
            
            # Process fixtures
            for i, fixture in enumerate(match_elements[:50]):  # Limit to first 50 for testing
                try:
                    fixture_data = {
                        'fixture_text': fixture.text,
                        'event_url': None
                    }
                    
                    # Try to extract match URL
                    try:
                        if fixture.tag_name == 'a':
                            fixture_data['event_url'] = fixture.get_attribute('href')
                        else:
                            link = fixture.find_element(By.XPATH, ".//a[contains(@href, '/event/')]")
                            fixture_data['event_url'] = link.get_attribute('href')
                    except:
                        pass
                    
                    # Only add fixtures with meaningful data
                    if fixture_data['fixture_text']:
                        print(f"Fixture {i+1}: {fixture_data['fixture_text'][:50]}...")
                        
                        # Try to parse teams and date from text
                        lines = fixture_data['fixture_text'].strip().split('\n')
                        if len(lines) >= 2:
                            for j, line in enumerate(lines):
                                if ' - ' in line:
                                    teams = line.split(' - ')
                                    if len(teams) == 2:
                                        fixture_data['home_team'] = teams[0].strip()
                                        fixture_data['away_team'] = teams[1].strip()
                                elif ':' in line and len(line) < 10:  # Probable score
                                    fixture_data['score'] = line.strip()
                                elif any(month in line.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                                    fixture_data['date'] = line.strip()
                        
                        league_data['fixtures'].append(fixture_data)
                except Exception as e:
                    print(f"Error processing fixture {i+1}: {e}")
            
            print(f"Processed {len(league_data['fixtures'])} fixtures")
            
            # Save page source for debugging
            with open(f"{league_name_lower.replace(' ', '_')}_fixtures_source.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            # Cache the fixture data
            self._cache_data(cache_filename, league_data)
            
            return league_data
        
        except Exception as e:
            print(f"Error fetching league fixtures: {e}")
            return None
    
    def get_team_fixtures(self, team_name, season_year="2022-2023", force_refresh=False):
        """
        Get all fixtures for a specific team and season.
        
        Args:
            team_name (str): Name of the team (e.g., "Manchester City")
            season_year (str): Season in format YYYY-YYYY (e.g., "2022-2023")
            force_refresh (bool): If True, ignore cache and fetch fresh data
            
        Returns:
            dict: Dictionary with team fixtures
        """
        # Normalize team name
        team_name_lower = team_name.lower()
        
        # Get team ID
        team_id = self.team_ids.get(team_name_lower)
        if not team_id:
            print(f"Team ID not found for {team_name}")
            return None
        
        # Check cache first
        cache_filename = f"{team_name_lower.replace(' ', '_')}_{season_year}_team_fixtures.json"
        if not force_refresh:
            cached_data = self._get_cached_data(cache_filename)
            if cached_data:
                print(f"Using cached fixture data for {team_name} ({season_year})")
                return cached_data
        
        # Initialize team data
        team_data = {
            'team_name': team_name,
            'team_id': team_id,
            'season': season_year,
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'fixtures': []
        }
        
        try:
            # Try to access the matches/schedule section directly
            team_url = f"https://www.sofascore.com/team/football/{team_name.replace(' ', '-').lower()}/{team_id}/results"
            print(f"Accessing team results at: {team_url}")
            
            self.driver.get(team_url)
            self._random_delay(5, 7)
            
            # Take screenshot for debugging
            self.driver.save_screenshot(f"{team_name_lower.replace(' ', '_')}_results_page.png")
            
            # Try to find season selector and select the correct season
            try:
                # Look for season dropdown or selector
                season_selector = self.driver.find_element(By.XPATH, 
                    "//select | //div[contains(text(), 'Season') or contains(text(), season_year)]")
                season_selector.click()
                self._random_delay(1, 2)
                
                # Try to select the specific season
                season_option = self.driver.find_element(By.XPATH, 
                    f"//option[contains(text(), '{season_year}')] | //div[contains(text(), '{season_year}')]")
                season_option.click()
                self._random_delay(3, 5)
                print(f"Selected season: {season_year}")
            except Exception as e:
                print(f"Could not select season: {e}")
                print("Continuing with default season...")
            
            # Now find the fixtures/matches
            # Try different selectors to find matches
            match_selectors = [
                "//div[contains(@class, 'event')]",
                "//a[contains(@href, '/event/')]",
                "//div[contains(@class, 'rows')]//div[contains(@class, 'row')]",
                "//div[contains(@data-id, 'event')]",
                "//div[contains(@class, 'match')]"
            ]
            
            match_elements = []
            for selector in match_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"Found {len(elements)} potential fixture elements with selector: {selector}")
                    match_elements = elements
                    break
            
            if not match_elements:
                print("No fixture elements found with any selector")
                # Try to get any useful links from the page
                links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/event/')]")
                if links:
                    print(f"Found {len(links)} direct event links")
                    for i, link in enumerate(links[:20]):
                        try:
                            href = link.get_attribute('href')
                            if href and '/event/' in href:
                                team_data['fixtures'].append({
                                    'event_url': href,
                                    'fixture_text': link.text or f"Event {i+1}"
                                })
                        except:
                            pass
            
            # Process matches/fixtures
            for i, match in enumerate(match_elements[:50]):  # Limit to first 50 for testing
                try:
                    match_data = {
                        'fixture_text': match.text,
                        'event_url': None
                    }
                    
                    # Try to extract match URL
                    try:
                        if match.tag_name == 'a':
                            match_data['event_url'] = match.get_attribute('href')
                        else:
                            link = match.find_element(By.XPATH, ".//a[contains(@href, '/event/')]")
                            match_data['event_url'] = link.get_attribute('href')
                    except:
                        # Try to get the match ID from attributes and construct URL
                        try:
                            match_id = match.get_attribute('data-id') or match.get_attribute('id')
                            if match_id and match_id.isdigit():
                                match_data['event_url'] = f"https://www.sofascore.com/event/{match_id}"
                        except:
                            pass
                    
                    # Only add matches with meaningful data
                    if match_data['fixture_text'] or match_data['event_url']:
                        team_data['fixtures'].append(match_data)
                        print(f"Match {i+1}: {match_data['fixture_text'][:50]}...")
                
                except Exception as e:
                    print(f"Error processing match {i+1}: {e}")
            
            print(f"Processed {len(team_data['fixtures'])} matches/fixtures")
            
            # Try to parse match data for reporting
            for fixture in team_data['fixtures']:
                if fixture.get('fixture_text'):
                    # Try to extract teams and scores from text
                    lines = fixture['fixture_text'].strip().split('\n')
                    for line in lines:
                        # Look for team names and score
                        if ' - ' in line:
                            parts = line.split(' - ')
                            if len(parts) == 2:
                                fixture['home_team'] = parts[0].strip()
                                fixture['away_team'] = parts[1].strip()
                        elif ':' in line and len(line) < 10:  # Likely a score
                            fixture['score'] = line.strip()
                        elif any(month in line.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            fixture['date'] = line.strip()
            
            # Cache the team fixture data
            self._cache_data(cache_filename, team_data)
            
            return team_data
        
        except Exception as e:
            print(f"Error fetching team fixtures: {e}")
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
                'has_xg': False,
                'home_xg': None,
                'away_xg': None,
                'statistics': {}
            }
            
            # Extract basic match information
            try:
                # Try to find team names and score
                team_name_elements = self.driver.find_elements(By.XPATH, 
                    "//div[contains(@class, 'participant') or contains(@class, 'team-name')]")
                
                if len(team_name_elements) >= 2:
                    match_details['home_team'] = team_name_elements[0].text
                    match_details['away_team'] = team_name_elements[1].text
                
                # Score
                score_element = self.driver.find_element(By.XPATH, 
                    "//div[contains(@class, 'score') or contains(@class, 'result')]")
                match_details['score'] = score_element.text
                
                # Date
                date_element = self.driver.find_element(By.XPATH, 
                    "//div[contains(@class, 'date') or contains(@class, 'time')]")
                match_details['date'] = date_element.text
                
                # Competition
                try:
                    competition_element = self.driver.find_element(By.XPATH, 
                        "//div[contains(@class, 'tournament') or contains(@class, 'competition')]")
                    match_details['competition'] = competition_element.text
                except:
                    # Try alternate method to find competition
                    try:
                        breadcrumb = self.driver.find_element(By.XPATH, "//div[contains(@class, 'breadcrumb')]")
                        match_details['competition'] = breadcrumb.text
                    except:
                        pass
            
            except Exception as e:
                print(f"Error extracting basic match info: {e}")
            
            # Now look for statistics tab and click it to get xG
            try:
                # First check if we can find the statistics tab
                tabs = self.driver.find_elements(By.XPATH, 
                    "//div[contains(text(), 'Statistics') or contains(text(), 'Stats')]")
                
                stats_tab = None
                for tab in tabs:
                    if 'Statistics' in tab.text or 'Stats' in tab.text:
                        stats_tab = tab
                        break
                
                if stats_tab:
                    print("Found statistics tab, clicking it...")
                    stats_tab.click()
                    self._random_delay(2, 3)
                    
                    # Take screenshot of statistics tab
                    self.driver.save_screenshot(f"match_{match_id}_stats.png")
                    
                    # Now look for xG statistics specifically
                    try:
                        xg_element = self.driver.find_element(By.XPATH, 
                            "//div[contains(text(), 'Expected goals') or contains(text(), 'xG')]")
                        
                        # Found xG element, now get the values
                        print("Found xG element")
                        match_details['has_xg'] = True
                        
                        # Now try to get the actual xG values
                        # This depends on the page structure, so we'll try several approaches
                        
                        # Try to find parent element that contains xG values
                        xg_row = xg_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'row') or contains(@class, 'stat')]")
                        
                        # Try to find the actual values
                        value_elements = xg_row.find_elements(By.XPATH, 
                            ".//div[contains(@class, 'value') or contains(@class, 'score')]")
                        
                        if len(value_elements) >= 2:
                            try:
                                # Try to convert to float, but store as text if not possible
                                home_text = value_elements[0].text
                                away_text = value_elements[1].text
                                
                                match_details['home_xg'] = float(home_text) if home_text and home_text.replace('.', '').isdigit() else home_text
                                match_details['away_xg'] = float(away_text) if away_text and away_text.replace('.', '').isdigit() else away_text
                                
                                print(f"xG values: {match_details['home_xg']} - {match_details['away_xg']}")
                            except:
                                # If we can't get individual values, at least store the text
                                match_details['xg_text'] = xg_row.text
                    
                    except Exception as e:
                        print(f"Error finding xG statistics: {e}")
                        match_details['has_xg'] = False
                
                else:
                    print("Statistics tab not found")
            
            except Exception as e:
                print(f"Error accessing statistics tab: {e}")
            
            # Cache the match details
            self._cache_data(cache_filename, match_details)
            
            return match_details
        
        except Exception as e:
            print(f"Error fetching match details: {e}")
            return None
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None

# Test the scraper
if __name__ == "__main__":
    scraper = SofaScoreDirectScraper()
    
    try:
        # Test with Premier League fixtures for 2022-2023 season
        print("Testing with Premier League 2022-2023 season...")
        league_fixtures = scraper.get_league_fixtures("Premier League", "2022-2023")
        
        if league_fixtures and league_fixtures['fixtures']:
            print(f"Found {len(league_fixtures['fixtures'])} league fixtures")
            
            # Try to get details for first fixture with URL
            for fixture in league_fixtures['fixtures']:
                if fixture.get('event_url'):
                    print(f"\nTesting match details for: {fixture.get('fixture_text', 'Unknown match')[:50]}...")
                    details = scraper.get_match_details(fixture['event_url'])
                    
                    if details:
                        print(f"Match: {details['home_team']} vs {details['away_team']}")
                        print(f"Score: {details['score']}")
                        print(f"Date: {details['date']}")
                        print(f"Has xG data: {details['has_xg']}")
                        if details['has_xg']:
                            print(f"xG: {details['home_xg']} - {details['away_xg']}")
                    
                    # Just test one fixture for now
                    break
        
        # Also test with Manchester City fixtures
        print("\nTesting with Manchester City 2022-2023 fixtures...")
        team_fixtures = scraper.get_team_fixtures("Manchester City", "2022-2023")
        
        if team_fixtures and team_fixtures['fixtures']:
            print(f"Found {len(team_fixtures['fixtures'])} team fixtures")
            
            # Print some sample fixtures
            for i, fixture in enumerate(team_fixtures['fixtures'][:5]):
                print(f"\nFixture {i+1}:")
                print(f"Text: {fixture.get('fixture_text', 'N/A')[:100]}...")
                print(f"URL: {fixture.get('event_url', 'N/A')}")
                print(f"Home: {fixture.get('home_team', 'N/A')}")
                print(f"Away: {fixture.get('away_team', 'N/A')}")
                print(f"Score: {fixture.get('score', 'N/A')}")
                print(f"Date: {fixture.get('date', 'N/A')}")
    
    finally:
        # Close the browser
        scraper.close()