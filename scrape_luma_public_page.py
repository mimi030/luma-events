# scrape_luma_public_page.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
from datetime import datetime
import os
import re

def get_attendee_count(driver, event_link_element):
    """Click event link and get attendee count from event page"""
    try:
        # Get the current window handle
        main_window = driver.current_window_handle
        
        # Click the event link to open in new tab
        ActionChains(driver).key_down(Keys.CONTROL).click(event_link_element).key_up(Keys.CONTROL).perform()
        
        # Wait for new tab and switch to it
        WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
        
        for handle in driver.window_handles:
            if handle != main_window:
                driver.switch_to.window(handle)
                break
        
        # Wait for event page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)
        
        # Look for "XX Went" text with multiple strategies
        attendee_count = None
        
        # Strategy 1: Look for specific class patterns
        went_selectors = [
            "[class*='title-label']",
            "[class*='card-title']", 
            "div:contains('Went')",
            "*[class*='stat']"
        ]
        
        # Strategy 2: Search all text for "Went" pattern
        try:
            page_text = driver.page_source
            went_matches = re.findall(r'(\d+)\s+Went', page_text, re.IGNORECASE)
            if went_matches:
                attendee_count = int(went_matches[0])
                print(f"    Found attendee count: {attendee_count}")
        except:
            pass
        
        # Strategy 3: Look through all elements containing "Went"
        if not attendee_count:
            try:
                went_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Went') or contains(text(), 'went')]")
                for elem in went_elements:
                    text = elem.text.strip()
                    match = re.search(r'(\d+)\s+[Ww]ent', text)
                    if match:
                        attendee_count = int(match.group(1))
                        print(f"    Found attendee count: {attendee_count}")
                        break
            except:
                pass
        
        if not attendee_count:
            print("    No attendee count found (event may be upcoming or private)")
        
        # Close the event tab and return to main window
        driver.close()
        driver.switch_to.window(main_window)
        
        return attendee_count
        
    except Exception as e:
        print(f"    Error getting attendee count: {e}")
        # Make sure we're back on main window
        try:
            driver.switch_to.window(main_window)
        except:
            pass
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
                    
                    # Look for event link element (for clicking)
                    link_element = None
                    link_url = None
                    try:
                        link_element = parent.find_element(By.CSS_SELECTOR, "a[href*='/']")
                        href = link_element.get_attribute('href')
                        if href and ('/e/' in href or 'lu.ma' in href):
                            link_url = href if href.startswith('http') else f"https://lu.ma{href}"
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
                    
                    # Get attendee count by clicking the event link
                    attendee_count = None
                    if link_element and link_url:
                        print(f"  Getting attendee count for: {title}")
                        attendee_count = get_attendee_count(driver, link_element)
                        time.sleep(2)  # Respectful delay
                    
                    events.append({
                        "title": title,
                        "time": event_time,
                        "location": location,
                        "url": link_url,
                        "attendee_count": attendee_count,
                        "scraped_at": datetime.now().isoformat()
                    })
                    
                    attendee_info = f" ({attendee_count} attendees)" if attendee_count else " (no attendee data)"
                    print(f"Found event: {title}{attendee_info}")
                    
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
                "events_with_attendee_count": len([e for e in events if e['attendee_count']]),
                "method": "selenium_with_click_navigation"
            }
        }
        
        with open('data/events.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully scraped {len(events)} events")
        events_with_counts = len([e for e in events if e['attendee_count']])
        print(f"Found attendee counts for {events_with_counts} events")
        
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
