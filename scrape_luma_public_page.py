# scrape_luma_public_page.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
from datetime import datetime
import os
import re

def get_attendee_count(driver, event_url):
    """Visit individual event page to get attendee count"""
    try:
        print(f"  Getting attendee count from: {event_url}")
        driver.get(event_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        
        # Look for "XX Went" text
        went_selectors = [
            "div[class*='title-label']:contains('Went')",
            "div:contains('Went')",
            "*[class*='card-title'] *:contains('Went')"
        ]
        
        # Try to find "XX Went" text
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Went')]")
        
        for elem in all_elements:
            text = elem.text.strip()
            # Look for pattern like "83 Went", "156 Went", etc.
            match = re.search(r'(\d+)\s+Went', text)
            if match:
                count = int(match.group(1))
                print(f"    Found attendee count: {count}")
                return count
        
        print("    No attendee count found")
        return None
        
    except Exception as e:
        print(f"    Error getting attendee count: {e}")
        return None

def scrape_luma_events():
    url = "https://lu.ma/mlto?period=past"
    
    # Setup headless Chrome for GitHub Actions
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=MLTO-EventBot/1.0 (volunteer@mlto.org)")
    
    try:
        # Use system chromium-chromedriver
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for page to load and events to appear
        print("Waiting for events to load...")
        WebDriverWait(driver, 15).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "h3")) > 0
        )
        
        time.sleep(5)  # Additional wait for dynamic content
        
        events = []
        
        # Find all h3 elements (event titles)
        h3_elements = driver.find_elements(By.TAG_NAME, "h3")
        print(f"Found {len(h3_elements)} h3 elements")
        
        for h3 in h3_elements:
            title = h3.text.strip()
            
            # Filter for actual event titles
            if (title and len(title) > 10 and 
                any(word in title.lower() for word in ['mlto', 'machine', 'learning', 'toronto', 'tech', 'ai', 'supercollider', 'cohere'])):
                
                try:
                    # Find parent container to get more details
                    parent = h3.find_element(By.XPATH, "./ancestor::div[contains(@class, 'content-card') or contains(@class, 'card-wrapper')]")
                    
                    # Look for event link
                    link = None
                    try:
                        link_elem = parent.find_element(By.CSS_SELECTOR, "a[href*='/']")
                        href = link_elem.get_attribute('href')
                        if href and ('/e/' in href or 'lu.ma' in href):
                            link = href if href.startswith('http') else f"https://lu.ma{href}"
                    except:
                        pass
                    
                    # Look for time
                    event_time = None
                    try:
                        time_elem = parent.find_element(By.CSS_SELECTOR, "span")
                        time_text = time_elem.text.strip()
                        if ':' in time_text and len(time_text) < 10:
                            event_time = time_text
                    except:
                        pass
                    
                    # Look for location
                    location = None
                    try:
                        text_elements = parent.find_elements(By.CSS_SELECTOR, "div")
                        for elem in text_elements:
                            text = elem.text.strip()
                            if (text and 'By ' not in text and 
                                any(venue in text for venue in ['Brewery', 'Bar', 'Exchange', 'Centre', 'Hall', 'Club'])):
                                location = text
                                break
                    except:
                        pass
                    
                    # Get attendee count from individual event page
                    attendee_count = None
                    if link:
                        attendee_count = get_attendee_count(driver, link)
                        time.sleep(3)  # Respectful delay between requests
                    
                    events.append({
                        "title": title,
                        "time": event_time,
                        "location": location,
                        "url": link,
                        "attendee_count": attendee_count,
                        "scraped_at": datetime.now().isoformat()
                    })
                    
                    print(f"Found event: {title} ({attendee_count} attendees)")
                    
                except Exception as e:
                    print(f"Error processing event '{title}': {e}")
                    continue
        
        driver.quit()
        
        # Save results
        os.makedirs('data', exist_ok=True)
        
        result = {
            "events": events,
            "debug_info": {
                "scraped_at": datetime.now().isoformat(),
                "url": url,
                "events_found": len(events),
                "method": "selenium_with_attendee_counts"
            }
        }
        
        with open('data/events.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully scraped {len(events)} events with attendee counts")
        
        for event in events:
            attendee_info = f" ({event['attendee_count']} attendees)" if event['attendee_count'] else ""
            print(f"- {event['title']}{attendee_info}")
        
        return len(events)
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        
        # Create error file
        os.makedirs('data', exist_ok=True)
        error_info = {
            "events": [],
            "error": str(e),
            "scraped_at": datetime.now().isoformat()
        }
        with open('data/events.json', 'w', encoding='utf-8') as f:
            json.dump(error_info, f, indent=2, ensure_ascii=False)
        
        return 0

if __name__ == "__main__":
    scrape_luma_events()
