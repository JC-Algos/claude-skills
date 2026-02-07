#!/usr/bin/env python3
"""
Fetch HSI constituents from AAStocks.com
"""

import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_from_aastocks():
    """Fetch HSI constituents from AAStocks"""
    
    url = "http://www.aastocks.com/en/stocks/market/index/hk-index-con.aspx"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print("🔍 Fetching HSI constituents from AAStocks.com...")
    print(f"URL: {url}")
    print()
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables on page")
        
        constituents = {}
        
        # Look for the constituent table
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                
                # Look for rows with stock code and name
                if len(cells) >= 2:
                    # Try to extract stock code
                    for i, cell in enumerate(cells):
                        text = cell.get_text(strip=True)
                        
                        # Check if this looks like a stock code (4-5 digits)
                        if re.match(r'^\d{4,5}$', text):
                            code = text.zfill(4)
                            symbol = f"{code}.HK"
                            
                            # Get name from next cell
                            if i + 1 < len(cells):
                                name = cells[i + 1].get_text(strip=True)
                                if name and len(name) > 2:
                                    constituents[symbol] = name
                                    print(f"  ✅ {symbol:12} {name}")
        
        if constituents:
            print()
            print(f"✅ Successfully fetched {len(constituents)} constituents from AAStocks")
            return constituents
        else:
            print("⚠️  No constituents found in table")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching from AAStocks: {e}")
        return None

def main():
    constituents = fetch_from_aastocks()
    
    if not constituents:
        print()
        print("❌ Failed to fetch from AAStocks. Keeping existing list.")
        return
    
    print()
    print("=" * 100)
    print(f"📊 HSI CONSTITUENTS FROM AASTOCKS ({len(constituents)} stocks)")
    print("=" * 100)
    
    # Sort by symbol
    sorted_constituents = dict(sorted(constituents.items()))
    
    for symbol, name in sorted_constituents.items():
        print(f"{symbol:12} {name}")
    
    # Save to JSON
    output_file = '/root/clawd/hsi_constituents.json'
    with open(output_file, 'w') as f:
        json.dump(sorted_constituents, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"💾 Saved to: {output_file}")
    print()
    
    # Verify Hang Seng Bank (0011.HK) is NOT in the list
    if '0011.HK' in constituents:
        print("⚠️  WARNING: Hang Seng Bank (0011.HK) is in the list!")
    else:
        print("✅ Confirmed: Hang Seng Bank (0011.HK) is NOT in the constituent list")
    
    print()

if __name__ == "__main__":
    main()
