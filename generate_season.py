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

def main():
    current_year = datetime.datetime.now().year
    
    parser = argparse.ArgumentParser(description="Master script to generate F1 championship animation for a given year.")
    parser.add_argument("--year", type=int, default=current_year, help=f"Season year to process (default: {current_year})")
    parser.add_argument("--force", action="store_true", help="Force refresh data even if it exists (default behavior for current year)")
    
    args = parser.parse_args()
    year = args.year
    
    import json

    data_filename = f'data/standings_history_{year}.json'
    data_exists = os.path.exists(data_filename)
    is_current_year = (year == current_year)
    
    # Determine if we need to fetch data
    should_fetch_data = False
    
    if args.force:
        print(f"Force refresh requested.")
        should_fetch_data = True
    elif is_current_year:
        print(f"Year {year} is the current season. Refreshing data...")
        should_fetch_data = True
    elif not data_exists:
        print(f"Data for {year} not found. Fetching...")
        should_fetch_data = True
    else:
        print(f"Data for historical year {year} already exists at {data_filename}. Skipping fetch.")
        should_fetch_data = False
        
    # 1. Fetch Data if needed
    if should_fetch_data:
        print(f"--- Running prepare_web_data for {year} ---")
        try:
            success = prepare_web_data.prepare_data(year)
            if not success:
                print("Data preparation returned False inside generate_season.py")
                sys.exit(1)
                
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
                print(f"Added {year} to seasons.json manifest.")
                
        except Exception as e:
            print(f"Error fetching data: {e}")
            sys.exit(1)
    
    # Check if data exists now (in case fetch failed silently or logic error)
    if not os.path.exists(data_filename):
         print(f"Error: {data_filename} was not created. Cannot proceed to animation.")
         sys.exit(1)

    # 2. Generate Animation
    print(f"--- Running animate_standings for {year} ---")
    try:
        animate_standings.animate(year)
    except Exception as e:
        print(f"Error generating animation: {e}")
        sys.exit(1)
        
    print("--- Done ---")
    
if __name__ == "__main__":
    main()
