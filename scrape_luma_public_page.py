# scrape_luma_events.py
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

def scrape_luma_events():
    url = "https://lu.ma/mlto"
    headers = {'User-Agent': 'MLTO-EventBot/1.0 (volunteer@mlto.org)'}
    
    try:
        response = requests.get(url, headers=headers)
        time.sleep(5)  # Respectful delay
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events = []
        
        # Look for event containers - inspect the page to find correct selectors
        # Common Luma selectors (adjust based on actual HTML structure):
        event_selectors = [
            'div[data-testid="event-card"]',
            '.event-card',
            '.event-item',
            'article',
            '[class*="event"]'
        ]
        
        for selector in event_selectors:
            event_cards = soup.select(selector)
            if event_cards:
                print(f"Found {len(event_cards)} events with selector: {selector}")
                break
        
        for event_card in event_cards:
            # Extract event details - adjust selectors based on actual HTML
            title_elem = (event_card.find('h1') or 
                         event_card.find('h2') or 
                         event_card.find('h3') or
                         event_card.find('[class*="title"]') or
                         event_card.find('[class*="name"]'))
            
            date_elem = (event_card.find('[class*="date"]') or
                        event_card.find('[class*="time"]') or
                        event_card.find('time'))
            
            location_elem = (event_card.find('[class*="location"]') or
                           event_card.find('[class*="venue"]') or
                           event_card.find('[class*="address"]'))
            
            link_elem = event_card.find('a')
            
            title = title_elem.get_text(strip=True) if title_elem else None
            date = date_elem.get_text(strip=True) if date_elem else None
            location = location_elem.get_text(strip=True) if location_elem else None
            link = link_elem.get('href') if link_elem else None
            
            if title:
                # Determine if event is upcoming or past based on date or section
                event_type = "unknown"
                parent_section = event_card.find_parent(['section', 'div'])
                if parent_section:
                    section_text = parent_section.get_text().lower()
                    if 'upcoming' in section_text or 'future' in section_text:
                        event_type = "upcoming"
                    elif 'past' in section_text or 'previous' in section_text:
                        event_type = "past"
                
                events.append({
                    "title": title,
                    "date": date,
                    "location": location,
                    "url": f"https://lu.ma{link}" if link and not link.startswith('http') else link,
                    "type": event_type,
                    "scraped_at": datetime.now().isoformat()
                })
        
        # Save to JSON file
        with open('data/events.json', 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        print(f"Scraped {len(events)} events from MLTO")
        
        # Print sample for debugging
        if events:
            print("Sample event:", events[0])
        
    except Exception as e:
        print(f"Error scraping: {e}")

if __name__ == "__main__":
    scrape_luma_events()
