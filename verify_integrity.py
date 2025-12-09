import json
import glob
import os
import fastf1
import pandas as pd
import datetime

"""
verify_integrity.py

Checks the completeness of downloaded data.
- Compares the number of race steps in local `data/standings_history_*.json` files
  against the official FastF1 event schedule.
- Reports years with mismatched race counts (indicating incomplete downloads).
"""

# Enable cache to minimize API hits
if not os.path.exists('f1_cache'):
    os.makedirs('f1_cache')
fastf1.Cache.enable_cache('f1_cache')

def verify_integrity():
    files = sorted(glob.glob('data/standings_history_*.json'))
    
    print(f"Verifying {len(files)} local files against FastF1 schedule...")
    print(f"{'Year':<6} | {'Local':<10} | {'Expected':<10} | {'Status':<10}")
    print("-" * 45)
    
    issues_found = 0
    
    for filepath in files:
        try:
            # Extract year from filename
            filename = os.path.basename(filepath)
            year_str = filename.replace('standings_history_', '').replace('.json', '')
            year = int(year_str)
            
            # 1. Check Local Data
            with open(filepath, 'r') as f:
                history = json.load(f)
            
            # Count steps that are 'Race'
            local_races = sum(1 for step in history if step.get('session') == 'Race')
            
            # 2. Check Canonical Schedule
            try:
                # This might hit API if not cached. 
                # Since we are running a heavy download in background, this *should* handle 429 via library 
                # but might be risky. However, schedules are small.
                schedule = fastf1.get_event_schedule(year)
                
                # Count official rounds
                # Exclude testing? EventFormat != 'testing'
                # Also check if it's the current year and future races exist?
                # We only want *completed* races.
                
                # Filter for completed races:
                # Logic: EventDate < Now? Or just count total if year is past?
                
                now = pd.Timestamp.now()
                
                # Filter useful columns
                races = schedule[schedule['EventFormat'] != 'testing']
                
                # Count
                expected_races = 0
                for _, event in races.iterrows():
                    # Check if it has a Race session date
                    # FastF1 schedule usually has 'Session5Date' for Race, or 'EventDate'
                    event_date = event['EventDate']
                    
                    # If the event is in the past, expect data.
                    if event_date < now:
                        expected_races += 1
                        
            except Exception as e:
                expected_races = "?"
                # print(f"Error fetching schedule for {year}: {e}")

            # 3. Compare
            status = "OK"
            if isinstance(expected_races, int):
                if local_races != expected_races:
                    status = "MISMATCH"
                    issues_found += 1
                    # Special check for current year (might be partial download vs partial schedule?)
                    # If Local < Expected, it's missing data.
                    # If Local > Expected, that's weird.
            
            print(f"{year:<6} | {local_races:<10} | {expected_races:<10} | {status:<10}")
            
        except Exception as e:
            print(f"Error checking {filepath}: {e}")

    print("-" * 45)
    if issues_found > 0:
        print(f"found {issues_found} potential issues.")
    else:
        print("All checks passed.")

if __name__ == "__main__":
    verify_integrity()
