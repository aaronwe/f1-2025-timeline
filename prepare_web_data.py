import fastf1
import pandas as pd
import os
import json
import argparse
import sys
import time

"""
prepare_web_data.py

Core logic for fetching and processing F1 data.
- Fetches season schedule and results using `fastf1`.
- Calculates cumulative standings points race-by-race.
- Enriches data with colors (from API or fallback).
- Outputs comprehensive JSON structure to `data/standings_history_{year}.json`.
- Raises `RateLimitExceededError` to allow upstream scripts to handle API limits.
"""

# Enable cache
if not os.path.exists('f1_cache'):
    os.makedirs('f1_cache')
fastf1.Cache.enable_cache('f1_cache')


class RateLimitExceededError(Exception):
    pass

def prepare_data(year):
    print(f"Fetching {year} Season Schedule...")
    try:
        schedule = fastf1.get_event_schedule(year)
    except Exception as e:
        msg = str(e).lower()
        if "429" in msg or "rate limit" in msg:
            raise RateLimitExceededError(f"Rate limit hit while fetching schedule for {year}: {e}")
        print(f"Error fetching schedule for {year}: {e}")
        return False

    # Initialize Ergast
    from fastf1.ergast import Ergast
    ergast = Ergast()
    
    # We will build a list of "steps". Each step is after a Round.
    # We no longer need to track cumulative_points manually.
    
    history = [] # List of steps
    
    for i, event in schedule.iterrows():
        round_num = event['RoundNumber']
        print(f"Processing Round {round_num}: {event['EventName']}")
        
        # 1. Fetch Official Standings from Ergast (with retry)
        # This handles dropped scores, half points, etc.
        standings_df = None
        retries = 0
        max_retries = 5
        
        while retries < max_retries:
            try:
                standings_resp = ergast.get_driver_standings(season=year, round=round_num)
                if not standings_resp.content:
                    print(f"  No standings data available for Round {round_num} yet.")
                    break
                    
                standings_df = standings_resp.content[0]
                break # Success
                
            except Exception as e:
                msg = str(e).lower()
                if "429" in msg or "rate limit" in msg or "too many requests" in msg:
                    wait_time = (2 ** retries) * 2 # Exponential backoff: 2, 4, 8, 16, 32
                    print(f"  Rate limit hit ({e}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    print(f"  Error fetching standings for Round {round_num}: {e}")
                    break
        
        if standings_df is None and retries >= max_retries:
             raise RateLimitExceededError(f"Ergast Rate limit exhausted after {max_retries} retries at Round {round_num}")
        
        if standings_df is None:
            continue # specific error logged above

        # 2. Fetch Race Session to get Team Colors (not in Ergast)
        # We only need the 'Race' session for this metadata.
        # We can try to be lightweight.
        
        color_map = {} # LastName -> {Color, TeamName}
        
        color_retries = 0
        max_color_retries = 3
        
        while color_retries < max_color_retries:
            try:
                session = fastf1.get_session(year, round_num, 'R')
                session.load(telemetry=False, weather=False, messages=False)
                
                if hasattr(session, 'results') and not session.results.empty:
                   for _, driver in session.results.iterrows():
                       # Normalize name for mapping
                       # Ergast uses 'givenName', 'familyName'. FastF1 uses 'LastName', 'FirstName'
                       lname = str(driver['LastName']).lower().strip()
                       
                       raw_color = driver.get('TeamColor', '')
                       color = f"#{raw_color}" if raw_color else None
                       team = driver.get('TeamName', 'Unknown')
                       
                       color_map[lname] = {'color': color, 'team': team}
                break # Success
                       
            except Exception as e:
                # If session load fails (e.g. rate limit), we might proceed without colors 
                # or raise if it's critical.
                msg = str(e).lower()
                if "429" in msg or "rate limit" in msg or "too many requests" in msg:
                     wait_time = (2 ** color_retries) * 5 
                     print(f"  FastF1 Rate limit hit ({e}). Retrying in {wait_time}s...")
                     time.sleep(wait_time)
                     color_retries += 1
                else:
                    print(f"  Warning: Could not fetch session data for colors ({e})")
                    break
                    
        if color_retries >= max_color_retries:
             print("  Warning: Skipped colors for this round due to rate limits.")

        # 3. Build Standings List
        current_standings = []
        
        for _, row in standings_df.iterrows():
            # Ergast fields: givenName, familyName, points, wins, constructorNames (list)
            first = row['givenName']
            last = row['familyName']
            points = float(row['points'])
            
            # Team Name from Ergast (list of constructors usually, take last/current)
            # Row constructorNames is a list.
            teams = row.get('constructorNames', [])
            team_name = teams[-1] if len(teams) > 0 else "Unknown"
            
            # Lookup Color
            # Try to match by last name
            lname_key = str(last).lower().strip()
            
            color = None
            if lname_key in color_map:
                color = color_map[lname_key]['color']
                # Prefer FastF1 team name if available as it might be more specific
                # But Ergast is fine too.
            
            # Fallback will be handled later if color is None
            
            # Special Exception for Michael Schumacher 1997 (DSQ)
            if year == 1997 and last == 'Schumacher' and first == 'Michael':
                 last = "Schumacher (DSQ)"
            
            name = f"{last}" # Display name style
            
            current_standings.append({
                'name': last,
                'firstName': first,
                'points': points,
                'team': team_name,
                'color': color,
                'rank': int(float(row['position'])) if pd.notna(row['position']) else 999
            })
            
        # Extract metadata
        event_date = str(event['EventDate'])
        try:
            dt = pd.to_datetime(event_date)
            date_str = dt.strftime("%d %b")
        except:
            date_str = str(event_date)

        location = event['Location']

        # Append to history
        # Note: We are now outputting one "step" per Round (Race), not separate Sprint/Race steps.
        # This is cleaner for the graph anyway.
        step_data = {
            'round': int(round_num),
            'eventName': event['EventName'],
            'session': 'Race', # Implies "Post-Race Standings"
            'date': date_str,
            'location': location,
            'standings': current_standings
        }
        history.append(step_data)
        print(f"  Recorded standings for Round {round_num}")
        
        # Pacing
        time.sleep(5.0)

    # Load Fallback Colors
    try:
        with open('fallback_teams.json', 'r') as f:
            fallback_colors = json.load(f)
    except FileNotFoundError:
        print("fallback_teams.json not found. Using empty fallback.")
        fallback_colors = {}

    for step in history:
        for driver in step['standings']:
            if not driver['color']:
                team = driver['team']
                # Try fallback
                if team in fallback_colors:
                    driver['color'] = fallback_colors[team]

    # Save to JSON in data directory
    if not os.path.exists('data'):
        os.makedirs('data')
        
    filename = f'data/standings_history_{year}.json'
    with open(filename, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"Saved {filename}")
    return True

if __name__ == "__main__":
    import datetime
    current_year = datetime.datetime.now().year
    
    parser = argparse.ArgumentParser(description="Clean F1 data for web visualization")
    parser.add_argument("--year", type=int, default=current_year, help=f"Season year to fetch (default: {current_year})")
    args = parser.parse_args()
    
    try:
        prepare_data(args.year)
    except RateLimitExceededError as e:
        print(f"CRITICAL: {e}")
        sys.exit(1)
