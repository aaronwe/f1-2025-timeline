import pandas as pd
import json
import glob
import os
import requests
import re
import io
from difflib import SequenceMatcher

"""
verify_points.py

Verifies the final point totals of the Top 3 drivers for each season against Wikipedia data.
- Scrapes Wikipedia for the season's final standings table.
- Compares points with local `data/standings_history_{year}.json`.
- Reports mismatches.
"""

def normalize_name(name):
    """Normalize driver names for comparison (remove accents, etc)"""
    # Simple normalization: lowercase and remove special chars
    # This might need to be more robust
    import unicodedata
    n = unicodedata.normalize('NFKD', str(name)).encode('ASCII', 'ignore').decode('utf-8')
    return n.lower().strip()

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_wiki_standings(year):
    url = f"https://en.wikipedia.org/wiki/{year}_Formula_One_season"
    
    try:
        # Use requests with User-Agent to avoid 403
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        
        tables = pd.read_html(io.StringIO(r.text), match="Driver") 
    except Exception as e:
        print(f"  Error fetching/parsing Wiki for {year}: {e}")
        return None

    # Find the right table. Usually "World Drivers' Championship standings"
    # It often has columns "Pos", "Driver", "Points"
    target_table = None
    for df in tables:
        cols = [str(c).lower() for c in df.columns]
        # Check for typical columns in standings table
        if 'driver' in cols and ('points' in cols or 'pts' in cols or 'total' in cols):
             # Some older tables might use "Total" for points
             target_table = df
             break
            
    if target_table is None:
        # Fallback: Try match="Pos"
        try:
             tables = pd.read_html(io.StringIO(r.text), match="Pos")
             for df in tables:
                cols = [str(c).lower() for c in df.columns]
                if 'driver' in cols:
                    target_table = df
                    break
        except:
            pass
            
    if target_table is None:
        print(f"  Could not find standings table for {year}")
        return None
        
    # Process top 3
    # Rename columns for consistency: lowercase, remove punctuation, remove brackets
    target_table.columns = [
        re.sub(r'\[.*?\]', '', str(c)).lower().replace('.', '').strip() 
        for c in target_table.columns
    ]
    
    # print(f"DEBUG: Found table with cols: {target_table.columns}")
    
    wiki_top3 = []
    
    count = 0
    for idx, row in target_table.iterrows():
        try:
            driver = row.get('driver', '')
            driver = re.sub(r'\[.*?\]', '', str(driver)).strip()
            
            # Points might be in 'points', 'pts', or 'total'
            points = row.get('points', row.get('pts', row.get('total', 0)))
            
            # print(f"DEBUG: Raw driver: {driver}, Raw points: {points}")

            # Ensure points is numeric
            try:
                pt_str = str(points).split('[')[0] 
                match = re.search(r'([\d\.]+)', pt_str)
                if match:
                    points = float(match.group(1))
                else:
                    points = 0.0
            except:
                continue 
                
            wiki_top3.append({'driver': driver, 'points': points})
            count += 1
            if count >= 3:
                break
        except:
            continue
            
    return wiki_top3

def get_local_top3(year):
    filename = f"data/standings_history_{year}.json"
    if not os.path.exists(filename):
        return None
        
    with open(filename, 'r') as f:
        history = json.load(f)
        
    if not history:
        return None
        
    # Get the last round
    last_round = history[-1]
    standings = last_round.get('standings', [])
    
    # Sort by points descending 
    sorted_standings = sorted(standings, key=lambda x: float(x['points']), reverse=True)
    
    local_top3 = []
    for i in range(min(3, len(sorted_standings))):
        s = sorted_standings[i]
        
        # Flattened structure: name (Last), firstName
        first = s.get('firstName', '')
        last = s.get('name', '')
        name = f"{first} {last}".strip()
            
        local_top3.append({
            'driver': name,
            'points': float(s['points'])
        })
        
    return local_top3

def verify_points():
    years = sorted([int(f.replace('data/standings_history_', '').replace('.json', '')) 
                    for f in glob.glob('data/standings_history_*.json')])
    
    issues = []
    
    print(f"{'Year':<6} | {'Driver':<20} | {'Wiki':<8} | {'Local':<8} | {'Status'}")
    print("-" * 65)

    for year in years:
        if year < 1950 or year > 2025: continue # Full history check
        
        # print(f"Checking {year}...")
        wiki_data = get_wiki_standings(year)
        local_data = get_local_top3(year)
        
        if not wiki_data or not local_data:
            print(f"{year:<6} | {'SKIP (No Data)':<45}")
            continue
            
        # Compare Top 3
        # Match by name first
        
        year_status = "OK"
        
        for i in range(min(len(wiki_data), len(local_data))):
            w = wiki_data[i]
            l = local_data[i]
            
            # Fuzzy match names
            name_score = similar(normalize_name(w['driver']), normalize_name(l['driver']))
            
            # Points match?
            # Float comparison with tolerance
            points_match = abs(w['points'] - l['points']) < 0.1
            
            status = "OK"
            if name_score < 0.6:
                status = "NAME MISMATCH"
                year_status = "FAIL"
            elif not points_match:
                status = "POINTS MISMATCH"
                year_status = "FAIL"
            
            if status != "OK":
                print(f"{year:<6} | {l['driver']:<20} | {w['points']:<8} | {l['points']:<8} | {status}")
                issues.append({'year': year, 'driver': l['driver'], 'wiki': w['points'], 'local': l['points']})
                
        if year_status == "OK":
             print(f"{year:<6} | {'All Match':<20} | {'-':<8} | {'-':<8} | OK")

    print("-" * 65)
    print(f"Verification complete. Found {len(issues)} issues.")
    
    if issues:
        with open('logs/points_mismatches.json', 'w') as f:
            json.dump(issues, f, indent=2)
        print("Mismatches saved to logs/points_mismatches.json")

if __name__ == "__main__":
    verify_points()
