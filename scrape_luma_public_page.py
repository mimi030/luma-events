# scrape_luma_events.py
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os

def scrape_luma_events():
    # Scrape both upcoming and past events
    urls = {
        "past": "https://lu.ma/mlto?period=past",
        "upcoming": "https://lu.ma/mlto"
    }
    
    headers = {'User-Agent': 'MLTO-EventBot/1.0 (volunteer@mlto.org)'}
    all_events = []
    
    for period, url in urls.items():
        try:
            print(f"Fetching {period} events from {url}")
            response = requests.get(url, headers=headers)
            time.sleep(5)  # Respectful delay
            
            if response.status_code != 200:
                print(f"Failed to fetch {period} events: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Luma events
            selectors = [
                'a[href*="/e/"]',  # Event links
                '[data-testid*="event"]',
                '[class*="event"]'
            ]
            
            events_found = 0
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"Found {len(elements)} elements with {selector}")
                    
                    for elem in elements:
                        title = elem.get_text(strip=True)
                        link = elem.get('href')
                        
                        if title and link and '/e/' in link:
                            all_events.append({
                                "title": title,
                                "url": f"https://lu.ma{link}" if not link.startswith('http') else link,
                                "period": period,
                                "scraped_at": datetime.now().isoformat()
                            })
                            events_found += 1
                    
                    if events_found > 0:
                        break
            
            print(f"Scraped {events_found} {period} events")
            
        except Exception as e:
            print(f"Error scraping {period} events: {e}")
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Save to JSON
    with open('data/events.json', 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    
    print(f"Total events scraped: {len(all_events)}")
    return len(all_events)

if __name__ == "__main__":
    scrape_luma_events()
