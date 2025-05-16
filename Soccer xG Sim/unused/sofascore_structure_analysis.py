"""
sofascore_structure_analysis.py
Author: Arya Chakraborty

This script helps us understand the HTML structure of the team page.
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import json

def analyze_team_page():
    """Analyze the structure of a SofaScore team page."""
    
    print("Setting up Chrome browser...")
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        # Access Manchester City's team page
        print("Accessing Manchester City team page...")
        driver.get("https://www.sofascore.com/team/football/manchester-city/17")
        time.sleep(5)
        
        # Take a screenshot for reference
        driver.save_screenshot("manchester_city_full_page.png")
        print("Saved screenshot of full page")
        
        # Find and analyze page structure
        print("\nAnalyzing page structure...")
        
        # 1. Team header information
        try:
            team_header = driver.find_element(By.XPATH, "//div[contains(@class, 'sc-')]//h2[contains(text(), 'Manchester City')]/..")
            print("\nTeam Header found:")
            print(f"- Text: {team_header.text}")
            print(f"- Class names: {team_header.get_attribute('class')}")
        except Exception as e:
            print(f"Couldn't find team header: {e}")
        
        # 2. Look for tabs or navigation elements
        try:
            tabs = driver.find_elements(By.XPATH, "//div[contains(@class, 'sc-')]//a[contains(@class, 'sc-') or contains(@role, 'tab')]")
            print(f"\nFound {len(tabs)} potential navigation tabs:")
            for i, tab in enumerate(tabs[:5]):  # Show first 5 only
                print(f"Tab {i+1}: Text = '{tab.text}', Class = '{tab.get_attribute('class')}'")
        except Exception as e:
            print(f"Couldn't find tabs: {e}")
        
        # 3. Find match containers
        try:
            # Try different XPath patterns to find match elements
            patterns = [
                "//div[contains(@class, 'event') or contains(@class, 'match')]",
                "//div[contains(@class, 'event-list')]//div",
                "//div[contains(@class, 'sc-')]//a[contains(@href, '/event/')]",
                "//div[contains(@class, 'sc-')]//div[.//div[contains(text(), 'vs')]]"
            ]
            
            for pattern in patterns:
                elements = driver.find_elements(By.XPATH, pattern)
                if elements:
                    print(f"\nFound {len(elements)} potential match elements using pattern: {pattern}")
                    for i, el in enumerate(elements[:3]):  # Show first 3 only
                        print(f"Match {i+1}:")
                        print(f"- Text: {el.text[:100]}...")
                        print(f"- Class: {el.get_attribute('class')}")
                        try:
                            href = el.get_attribute('href')
                            if href:
                                print(f"- Link: {href}")
                        except:
                            pass
                    break
            else:
                print("\nNo match elements found with any pattern")
        
        except Exception as e:
            print(f"Error finding match elements: {e}")
        
        # 4. Try to find the seasons dropdown or selector
        try:
            season_selectors = driver.find_elements(By.XPATH, "//select | //div[contains(@class, 'dropdown') or contains(@class, 'select')]")
            print(f"\nFound {len(season_selectors)} potential season selectors:")
            for i, sel in enumerate(season_selectors[:3]):
                print(f"Selector {i+1}: Text = '{sel.text}', Class = '{sel.get_attribute('class')}'")
        except Exception as e:
            print(f"Couldn't find season selector: {e}")
        
        # 5. Extract and save the page source for offline analysis
        source = driver.page_source
        with open("team_page_source.html", "w", encoding="utf-8") as f:
            f.write(source)
        print("\nSaved page source to team_page_source.html")
        
        # 6. Get all links on the page to analyze available endpoints
        links = driver.find_elements(By.XPATH, "//a[@href]")
        hrefs = [link.get_attribute('href') for link in links if link.get_attribute('href')]
        
        # Filter for interesting links
        match_links = [href for href in hrefs if '/event/' in href]
        player_links = [href for href in hrefs if '/player/' in href]
        season_links = [href for href in hrefs if '/season/' in href]
        
        links_data = {
            'match_links': match_links[:10],  # First 10 only
            'player_links': player_links[:10],
            'season_links': season_links[:10]
        }
        
        with open("page_links.json", "w") as f:
            json.dump(links_data, f, indent=2)
        
        print("\nSaved interesting links to page_links.json")
        print(f"- Match links: {len(match_links)}")
        print(f"- Player links: {len(player_links)}")
        print(f"- Season links: {len(season_links)}")
        
        print("\nAnalysis completed!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
    
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    analyze_team_page()