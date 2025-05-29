"""
understat_access_test.py - Test access to Understat
Author: Arya Chakraborty

This script tests whether you can successfully connect to Understat 
and retrieve basic page content without being blocked.

This did not end up working because understat has a lot of anti-scraping measures in place.
"""

import requests
import time
import random

def test_understat_access():
    """Test if we can access Understat without being blocked."""
    
    # URLs to test (from less sensitive to more sensitive)
    test_urls = [
        "https://understat.com/",  # Home page
        "https://understat.com/league/EPL/2022",  # League overview
        "https://understat.com/team/Manchester_United/2022"  # Team page
    ]
    
    # Different user agents to try
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/112.0'
    ]
    
    # Try each URL with each user agent
    results = []
    
    for url in test_urls:
        for user_agent in user_agents:
            print(f"\nTesting: {url}")
            print(f"User-Agent: {user_agent}")
            
            # Set up session with headers
            session = requests.Session()
            session.headers.update({
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            try:
                # Add a delay to be respectful
                time.sleep(random.uniform(3, 5))
                
                # Make request
                response = session.get(url)
                
                # Check status
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    content_length = len(response.text)
                    print(f"Content Length: {content_length} characters")
                    
                    # Check for typical block indicators
                    if "captcha" in response.text.lower() or "blocked" in response.text.lower():
                        print("WARNING: Page might include captcha or block message!")
                        success = False
                    else:
                        # Check if it looks like a normal page
                        normal_indicators = [
                            "<title>Understat", 
                            "table-responsive",
                            "main-navbar"
                        ]
                        if any(indicator in response.text for indicator in normal_indicators):
                            print("SUCCESS: Page appears to be normal content")
                            success = True
                        else:
                            print("WARNING: Page doesn't look like normal content!")
                            success = False
                else:
                    print(f"Failed with status code: {response.status_code}")
                    success = False
                
                results.append({
                    'url': url,
                    'user_agent': user_agent,
                    'status_code': response.status_code,
                    'success': success
                })
                
            except Exception as e:
                print(f"Error: {e}")
                results.append({
                    'url': url,
                    'user_agent': user_agent,
                    'status_code': 'Error',
                    'success': False
                })
    
    # Print summary
    print("\n===== TEST SUMMARY =====")
    success_count = sum(1 for r in results if r['success'])
    print(f"{success_count}/{len(results)} tests passed\n")
    
    for i, result in enumerate(results):
        print(f"Test {i+1}: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
        print(f"  URL: {result['url']}")
        print(f"  User-Agent: {result['user_agent'][:30]}...")
        print(f"  Status: {result['status_code']}")
        print()
    
    # Final recommendation
    if success_count > 0:
        print("RECOMMENDATION: Some tests successful. You can proceed with creating the scraper.")
        print("Use the successful user agent(s) in your implementation.")
        successful_agents = [r['user_agent'] for r in results if r['success']]
        if successful_agents:
            print(f"Best User-Agent: {successful_agents[0]}")
    else:
        print("RECOMMENDATION: All tests failed. Consider:")
        print("1. Trying again later")
        print("2. Using a different website")
        print("3. Using a proxy or VPN")
        print("4. Using an API instead of scraping")

if __name__ == "__main__":
    test_understat_access()