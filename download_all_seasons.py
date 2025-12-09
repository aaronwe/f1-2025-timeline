import argparse
import os
import json
import time

"""
download_all_seasons.py

Orchestrates the bulk download of historical F1 data.
- Iterates through a specified range of years (default 1950-2025).
- Checks `data/download_progress.json` to skip already completed years.
- Calls `prepare_web_data.py` to fetch and process each season.
- Implements rate-limiting and pacing strategies to stay within FastF1/ergast API limits.
"""

from prepare_web_data import prepare_data, RateLimitExceededError

def download_seasons(start_year, end_year, force=False):
    print(f"Downloading data for seasons {start_year} to {end_year}...")
    
    # Ensure data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')

    manifest_path = 'data/seasons.json'
    progress_path = 'data/download_progress.json'
    
    # Load progress
    completed_years = []
    if os.path.exists(progress_path):
        try:
            with open(progress_path, 'r') as f:
                completed_years = json.load(f)
        except:
             print("Could not load download_progress.json, starting fresh.")

    # Target: ~7 seasons per hour => 1 season every ~514 seconds (approx 8.5 mins)
    # Let's say 600 seconds (10 mins) to be ultra safe.
    TARGET_CYCLE_TIME = 600 
    
    for year in range(start_year, end_year + 1):
        if year in completed_years and not force:
            print(f"Skipping {year}: Already marked as complete in progress log.")
            continue

        filename = f'data/standings_history_{year}.json'
        should_download = True
        
        # Validation Logic: Check if exists and has enough content
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                if len(data) > 5 and not force:
                    print(f"Skipping {year}: Already exists with {len(data)} rounds.")
                    should_download = False
                    
                    # Mark as complete if not already
                    if year not in completed_years:
                        completed_years.append(year)
                        with open(progress_path, 'w') as f:
                            json.dump(completed_years, f)
                else:
                    print(f"Retrying {year}: Exists but only has {len(data)} rounds (incomplete).")
            except Exception as e:
                print(f"Retrying {year}: File corrupted or unreadable ({e})")
        
        if should_download:
            print(f"\n--- Processing {year} ---")
            start_time = time.time()
            
            try:
                success = prepare_data(year)
                
                if success:
                    # Update manifest incrementally
                    current_seasons = []
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r') as f:
                            try:
                                current_seasons = json.load(f)
                            except:
                                pass
                    
                    if year not in current_seasons:
                        current_seasons.append(year)
                        current_seasons.sort(reverse=True)
                        with open(manifest_path, 'w') as f:
                            json.dump(current_seasons, f)
                    
                    # Mark as complete
                    if year not in completed_years:
                        completed_years.append(year)
                        with open(progress_path, 'w') as f:
                            json.dump(completed_years, f)
                    
                    print(f"Updated manifest and progress for {year}")
                
                # Check elapsed time
                elapsed = time.time() - start_time
                
                # If we actually did work (downloaded content), pace ourselves
                # prepare_data returns True if it ran. If it was cached inside prepare_data (fastf1 cache),
                # elapsed time will be small.
                
                print(f"Year {year} processed in {elapsed:.2f}s")
                
                if elapsed > 10: 
                    # Assume API calls were made
                    sleep_time = max(0, TARGET_CYCLE_TIME - elapsed)
                    print(f"PACING: Sleeping for {sleep_time:.1f}s to respect rate limit (~8 min cycle)...")
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                else:
                    print("Processing was likely cached or fast. Short sleep.")
                    time.sleep(2)
                    
            except RateLimitExceededError as e:
                print(f"\n!!! RATE LIMIT HIT !!!")
                print(f"Stopper at year {year}. Details: {e}")
                print("Exiting safely. Resume later by running this script again.")
                return # Exit function
                
            except Exception as e:
                print(f"Failed to process {year}: {e}")
                time.sleep(5) # Short sleep on error

if __name__ == '__main__':
    current_year = datetime.datetime.now().year
    
    parser = argparse.ArgumentParser(description="Download F1 data for multiple seasons")
    parser.add_argument("--start", type=int, default=1950, help="Start year (default: 1950)")
    parser.add_argument("--end", type=int, default=current_year, help=f"End year (default: {current_year})")
    
    parser.add_argument("--force", action="store_true", help="Force download even if file exists")
    
    args = parser.parse_args()
    
    download_seasons(args.start, args.end, args.force)
