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
    mismatched_years = []
    
    # Setup Logging
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/integrity_check_{timestamp}.txt"
    json_filename = "logs/mismatched_years.json"
    
    with open(log_filename, 'w') as log_file:
        def log(msg):
            print(msg)
            log_file.write(msg + "\n")
            
        log(f"Verifying {len(files)} local files against FastF1 schedule...")
        log(f"Log saved to: {log_filename}")
        
        header = f"{'Year':<6} | {'Local':<10} | {'Expected':<10} | {'Status':<10}"
        separator = "-" * 45
        log(header)
        log(separator)

        for filepath in files:
            try:
                # Extract year from filename
                filename = os.path.basename(filepath)
                year_str = filename.replace('standings_history_', '').replace('.json', '')
                year = int(year_str)
                
                # 1. Local Data Count
                with open(filepath, 'r') as f:
                    history = json.load(f)
                
                local_races = 0
                if history:
                    # In our structure, history is a list of race steps.
                    local_races = len(history)
                    
                # 2. Expected Data Count (FastF1)
                expected_races = 0
                try:
                    schedule = fastf1.get_event_schedule(year)
                    # Filter for completed races only (Session5Date < now or similar)
                    now = datetime.datetime.now()
                    
                    races = schedule
                    
                    # Count
                    expected_races = 0
                    for _, event in races.iterrows():
                        # Check if it has a Race session date
                        # FastF1 schedule usually has 'Session5Date' for Race, or 'EventDate'
                        event_date = event['EventDate']
                        
                        # If the event is in the past, expect data.
                        if event_date < now:
                            expected_races += 1
                            
                            # Check for Sprint
                            # FastF1 schedules identify sprints via EventFormat == 'sprint' (usually)
                            # The 'f1_2025_timeline' mentions sprints.
                            if 'EventFormat' in event and event['EventFormat'] == 'sprint':
                                expected_races += 1
                            # Check specifically for 2024/2025 where sprints are common
                            # If 'Session4' is Sprint for example.
                            # But checking EventFormat is safest if column exists.
                            
                except Exception as e:
                    msg = str(e).lower()
                    if "429" in msg or "too many requests" in msg:
                        log(f"  Rate limit hit for {year}. Waiting 30s...")
                        import time
                        time.sleep(30)
                        expected_races = "?"
                    else:
                        expected_races = "?"

                # 3. Compare
                status = "OK"
                if isinstance(expected_races, int):
                    if local_races != expected_races:
                        status = "MISMATCH"
                        issues_found += 1
                        mismatched_years.append(year)
                
                log(f"{year:<6} | {local_races:<10} | {expected_races:<10} | {status:<10}")
                
                # Be nice to the API
                import time
                time.sleep(2)
                
            except Exception as e:
                log(f"Error checking {filepath}: {e}")

        log("-" * 45)
        if issues_found > 0:
            log(f"found {issues_found} potential issues.")
            
            # Save mismatched years to JSON
            with open(json_filename, 'w') as jf:
                json.dump(mismatched_years, jf, indent=2)
            log(f"Saved list of {len(mismatched_years)} mismatched years to {json_filename}")
            
        else:
            log("All checks passed.")

if __name__ == "__main__":
    verify_integrity()
