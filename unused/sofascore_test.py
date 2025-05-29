"""
sofascore_test.py - Test access to sofascore
Author: Arya Chakraborty

This script verifies that we can access SofaScore and navigate to team pages.

This worked so we will proceed testing with sofascore.
In the end, scraping from this site will not work.
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def test_sofascore_access():
    """Test basic access to SofaScore."""
    
    print("Setting up Chrome browser...")
    
    # Set up Chrome options
    chrome_options = Options()
    # Uncomment the line below if you want to run headless (no browser window)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        # Access SofaScore homepage
        print("Accessing SofaScore homepage...")
        driver.get("https://www.sofascore.com/")
        time.sleep(5)  # Increased wait time for page to fully load
        
        # Check if we can access the homepage
        print(f"Page title: {driver.title}")
        if driver.title:
            print("Successfully accessed a page. Title found.")
        else:
            print("Warning: Page title is empty but page loaded.")
        
        # Let's get the current URL to verify we're on SofaScore
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        if "sofascore" in current_url.lower():
            print("URL confirms we're on SofaScore website")
        else:
            print("Warning: URL doesn't seem to be SofaScore")
        
        # Try to find the SofaScore logo or other distinctive element
        try:
            logo = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'logo') or contains(@class, 'header')]"))
            )
            print("Found site logo/header element")
        except Exception as e:
            print(f"Couldn't find logo: {e}")
            # Take a screenshot to see what's happening
            driver.save_screenshot("sofascore_page.png")
            print("Saved screenshot as sofascore_page.png")
        
        # Navigate to football section directly
        print("Navigating to football section directly...")
        driver.get("https://www.sofascore.com/football")
        time.sleep(5)
        print(f"Football page title: {driver.title}")
        print(f"Football page URL: {driver.current_url}")
        
        # Try to access a specific team (Manchester City)
        print("Accessing Manchester City team page...")
        driver.get("https://www.sofascore.com/team/football/manchester-city/17")
        time.sleep(5)
        print(f"Team page title: {driver.title}")
        print(f"Team page URL: {driver.current_url}")
        
        # Try to find the team name on the page
        try:
            page_source = driver.page_source
            if "Manchester City" in page_source:
                print("Found 'Manchester City' in page source")
            else:
                print("Warning: Team name not found in page source")
            
            # Look for any match elements
            matches = driver.find_elements(By.XPATH, "//div[contains(@class, 'Event') or contains(@class, 'Match')]")
            print(f"Found {len(matches)} potential match elements")
            
            if matches:
                print("\nText from first potential match element:")
                print(matches[0].text[:200] + "..." if len(matches[0].text) > 200 else matches[0].text)
        except Exception as e:
            print(f"Error finding elements: {e}")
            driver.save_screenshot("manchester_city_page.png")
            print("Saved screenshot as manchester_city_page.png")
        
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Error during test: {e}")
        # Take a screenshot when an error occurs
        try:
            driver.save_screenshot("error_screenshot.png")
            print("Saved error screenshot as error_screenshot.png")
        except:
            pass
    
    finally:
        # Close the browser
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    test_sofascore_access()