# scrape_luma_public_page.py
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os

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
            
            # Try to find any event cards with different selectors
            alternative_selectors = [
                'div[class*="content-card"]',
                'div[class*="event"]',
                'a[href*="/e/"]',
                'h3',
                '[aria-label*="event" i]'
            ]
            
            for selector in alternative_selectors:
                elements = soup.select(selector)
                print(f"Selector '{selector}': found {len(elements)} elements")
                
                if elements and len(elements) > 0:
                    for elem in elements[:3]:  # Show first 3
                        text = elem.get_text(strip=True)[:100]
                        print(f"  Sample: {text}")
        
        # Original scraping logic
        for section in timeline_sections:
            date_elem = section.find('div', class_='jsx-3191908726 date')
            date = date_elem.get_text(strip=True) if date_elem else None
            
            event_cards = section.find_all('div', class_='jsx-702bb7b3285aa34f jsx-1544432796 content-card')
            
            for card in event_cards:
                title_elem = card.find('h3', class_='jsx-3672995585')
                title = title_elem.get_text(strip=True) if title_elem else None
                
                link_elem = card.find('a', class_='event-link content-link')
                link = link_elem.get('href') if link_elem else None
                
                time_elem = card.find('span', class_='jsx-1305897383')
                event_time = time_elem.get_text(strip=True) if time_elem else None
                
                location_elem = card.find('div', class_='jsx-e74804ac03b83871 text-ellipses')
                location = None
                if location_elem:
                    location_divs = card.find_all('div', class_='jsx-e74804ac03b83871 text-ellipses')
                    for div in location_divs:
                        text = div.get_text(strip=True)
                        if 'By ' not in text and len(text) > 3:
                            location = text
                            break
                
                if title and link:
                    events.append({
                        "title": title,
                        "date": date,
                        "time": event_time,
                        "location": location,
                        "url": f"https://lu.ma{link}",
                        "scraped_at": datetime.now().isoformat()
                    })
        
        # Always create the file, even if empty
        os.makedirs('data', exist_ok=True)
        
        # Add debug info to JSON
        result = {
            "events": events,
            "debug_info": {
                "scraped_at": datetime.now().isoformat(),
                "url": url,
                "status_code": response.status_code,
                "page_length": len(response.text),
                "timeline_sections_found": len(timeline_sections),
                "events_found": len(events)
            }
        }
        
        with open('data/events.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Scraped {len(events)} events and saved to data/events.json")
        
        if events:
            for i, event in enumerate(events[:3]):
                print(f"Event {i+1}: {event['title']} - {event['date']}")
        else:
            print("No events found - check debug_info in JSON file")
        
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
