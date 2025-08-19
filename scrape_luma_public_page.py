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
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Find timeline sections with events
        timeline_sections = soup.find_all('div', class_='jsx-797115727 timeline-section')
        
        for section in timeline_sections:
            # Extract date from timeline title
            date_elem = section.find('div', class_='jsx-3191908726 date')
            date = date_elem.get_text(strip=True) if date_elem else None
            
            # Find event cards in this section
            event_cards = section.find_all('div', class_='jsx-702bb7b3285aa34f jsx-1544432796 content-card')
            
            for card in event_cards:
                # Extract event title
                title_elem = card.find('h3', class_='jsx-3672995585')
                title = title_elem.get_text(strip=True) if title_elem else None
                
                # Extract event link
                link_elem = card.find('a', class_='event-link content-link')
                link = link_elem.get('href') if link_elem else None
                
                # Extract time
                time_elem = card.find('span', class_='jsx-1305897383')
                event_time = time_elem.get_text(strip=True) if time_elem else None
                
                # Extract location
                location_elem = card.find('div', class_='jsx-e74804ac03b83871 text-ellipses')
                location = None
                if location_elem:
                    # Look for location (usually after the location icon)
                    location_divs = card.find_all('div', class_='jsx-e74804ac03b83871 text-ellipses')
                    for div in location_divs:
                        text = div.get_text(strip=True)
                        # Skip organizer info, look for venue names
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
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        
        # Save to JSON
        with open('data/events.json', 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        print(f"Scraped {len(events)} events and saved to data/events.json")
        
        # Print sample events
        for i, event in enumerate(events[:3]):
            print(f"Event {i+1}: {event['title']} - {event['date']}")
        
        return len(events)
        
    except Exception as e:
        print(f"Error scraping: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    scrape_luma_events()
