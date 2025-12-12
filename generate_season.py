import argparse
import os
import datetime
import sys

"""
generate_season.py

Master script for the F1 Standing Animation pipeline.
- Accepts a year as input.
- Checks if data exists in `data/`; if not (or if forced), fetches it via `prepare_web_data`.
- Updates the `data/seasons.json` manifest.
- Triggers `animate_standings.py` to generate the final MP4 animation.
"""

# Import the main functions from our other scripts
# We need to make sure they are importable. 
# Since they are in the same directory, this works.
import prepare_web_data
import animate_standings

def process_year(year, force):
    """
    Process a single year: fetch data if needed, then generate animation.
    Returns True if successful, False otherwise.
    """
    import json
    
    current_year = datetime.datetime.now().year
    data_filename = f'data/standings_history_{year}.json'
    data_exists = os.path.exists(data_filename)
    is_current_year = (year == current_year)
    
    # Determine if we need to fetch data
    should_fetch_data = False
    
    if force:
        print(f"[{year}] Force refresh requested.")
        should_fetch_data = True
    elif is_current_year:
        print(f"[{year}] Year {year} is the current season. Refreshing data...")
        should_fetch_data = True
    elif not data_exists:
        print(f"[{year}] Data not found. Fetching...")
        should_fetch_data = True
    else:
        print(f"[{year}] Data already exists at {data_filename}. Skipping fetch.")
        should_fetch_data = False
        
    # 1. Fetch Data if needed
    if should_fetch_data:
        print(f"[{year}] --- Running prepare_web_data ---")
        try:
            success = prepare_web_data.prepare_data(year)
            if not success:
                print(f"[{year}] Data preparation returned False.")
                return False
                
            # Update Manifest (seasons.json)
            manifest_path = 'data/seasons.json'
            current_seasons = []
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r') as f:
                        current_seasons = json.load(f)
                except:
                    pass
            
            if year not in current_seasons:
                current_seasons.append(year)
                current_seasons.sort(reverse=True)
                with open(manifest_path, 'w') as f:
                    json.dump(current_seasons, f)
                print(f"[{year}] Added to seasons.json manifest.")
                
        except Exception as e:
            print(f"[{year}] Error fetching data: {e}")
            return False
    
    # Check if data exists now
    if not os.path.exists(data_filename):
         print(f"[{year}] Error: {data_filename} was not created. Cannot proceed to animation.")
         return False

    # 2. Generate Animation
    print(f"[{year}] --- Running animate_standings ---")
    try:
        animate_standings.animate(year)
    except Exception as e:
        print(f"[{year}] Error generating animation: {e}")
        return False
        
    print(f"[{year}] --- Done ---")
    return True

def main():
    current_year = datetime.datetime.now().year
    
    parser = argparse.ArgumentParser(description="Master script to generate F1 championship animations for a range of years.")
    parser.add_argument("--year", type=int, help="Single season year to process (optional, overrides start/end)")
    parser.add_argument("--start", type=int, default=current_year, help=f"Start year (default: {current_year})")
    parser.add_argument("--end", type=int, default=current_year, help=f"End year (default: {current_year})")
    parser.add_argument("--force", action="store_true", help="Force refresh data even if it exists")
    
    args = parser.parse_args()
    
    # Determine range
    if args.year:
        start_year = args.year
        end_year = args.year
    else:
        start_year = args.start
        end_year = args.end
        
    if start_year > end_year:
        print(f"Error: Start year {start_year} is greater than end year {end_year}")
        sys.exit(1)
        
    print(f"Processing range: {start_year} to {end_year}")
    
    failures = []
    
    for year in range(start_year, end_year + 1):
        print(f"\n=== Processing Year {year} ===")
        success = process_year(year, args.force)
        
        if not success:
            failures.append(year)
            
    if failures:
        print("\n\nFinished with failures for years:", failures)
        sys.exit(1)
    else:
        print("\n\nAll requested years processed successfully.")

if __name__ == "__main__":
    main()
