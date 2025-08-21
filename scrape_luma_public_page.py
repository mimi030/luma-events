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
    headers = {'User-Agent': 'MLTO-EventBot/1.0 (volunteer@mlto.org)'}
    
    try:
        print(f"Fetching events from {url}")
        response = requests.get(url, headers=headers)
        time.sleep(5)  # Respectful delay
        
        if response.status_code != 200:
            print(f"Failed to fetch events: {response.status_code}")
            return 0
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug: Print page info
        print(f"Page title: {soup.title.string if soup.title else 'No title'}")
        print(f"Page content length: {len(response.text)}")
        
        # Debug: Look for any timeline sections
        timeline_sections = soup.find_all('div', class_='jsx-797115727 timeline-section')
        print(f"Found {len(timeline_sections)} timeline sections")
        
        # Debug: Look for any event-related elements
        event_links = soup.find_all('a', href=True)
        event_count = 0
        for link in event_links:
            if '/e/' in link.get('href', '') or 'event' in link.get('class', []):
                event_count += 1
        print(f"Found {event_count} potential event links")
        
        # Debug: Look for common class patterns
        jsx_elements = soup.find_all('div', class_=lambda x: x and 'jsx-' in str(x))
        print(f"Found {len(jsx_elements)} JSX elements")
        
        events = []
        
        # Try alternative selectors if timeline sections not found
        if not timeline_sections:
            print("No timeline sections found, trying alternative selectors...")
            
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
                        "date": date,
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
        
        # Always create the file, even if empty
        os.makedirs('data', exist_ok=True)
        
        # Add debug info to JSON
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
        print(f"Error scraping: {e}")
        import traceback
        traceback.print_exc()
        
        # Create error file
        os.makedirs('data', exist_ok=True)
        error_info = {
            "error": str(e),
            "scraped_at": datetime.now().isoformat(),
            "events": []
        }
        with open('data/events.json', 'w', encoding='utf-8') as f:
            json.dump(error_info, f, indent=2, ensure_ascii=False)
        
        return 0

if __name__ == "__main__":
    scrape_luma_events()
