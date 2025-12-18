import fastf1
import pandas as pd
import os
import json
import argparse
import sys
import time
import copy

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

import datetime

# [NEW] Aggressive HTTP Caching (User Request)
import requests_cache

import unicodedata

def normalize_name(text):
    """
    Normalizes a string to ASCII, lowercase, stripped.
    e.g. "Hülkenberg" -> "hulkenberg"
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Normalize unicode characters to closest ASCII equivalent
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return text.lower().strip()

class RateLimitExceededError(Exception):
    pass

def prepare_data(year):
    # Configure Cache based on year
    # Historical years: Cache forever
    # Current/Future years: Cache for 4 hours (14400s) to allow updates
    current_year = datetime.datetime.now().year
    expire_time = -1 if year < current_year else 14400
    
    requests_cache.install_cache('f1_http_cache', backend='sqlite', expire_after=expire_time)
    
    print(f"Fetching {year} Season Schedule... (Cache: {'Forever' if expire_time == -1 else '4h'})")
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
    
    # Iterate through rounds
    # Skip Round 0 (Pre-Season Testing) if present
    
    # Filter for valid rounds (1 to N)
    rounds = schedule[schedule['RoundNumber'] > 0]
    
    for _, event in rounds.iterrows():
        round_num = int(event['RoundNumber'])
        # if round_num > 5: break # Debug limit
        
        # 1. Fetch Standings AFTER this round
        # We need to retry this because Ergast generic rate limits are strict
        standings_df = None
        retries = 0
        max_retries = 5 
        
        while retries < max_retries:
            try:
                # Use fastf1 ergast wrapper
                resp = ergast.get_driver_standings(season=year, round=round_num)
                if resp.content and not resp.content[0].empty:
                    standings_df = resp.content[0]
                else:
                    print(f"  No standings data available for Round {round_num} yet.")
                    # If this is the current season, we might have reached the future.
                    # Stop processing smoothly.
                    return True # Success so far
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

        # [NEW] SPRINT LOGIC
        # CHECK FOR SPRINT RESULTS
        sprint_step_data = None
        sprint_points_map = {} # Driver FamilyName -> Points earned in sprint
        sprint_results_map = {} # Driver FamilyName -> Result Display String (e.g. "1", "DNF")

        try:
            sprint_resp = ergast.get_sprint_results(season=year, round=round_num)
            if sprint_resp.content and not sprint_resp.content[0].empty:
                sprint_df = sprint_resp.content[0]
                print(f"  Found Sprint results for Round {round_num}")
                
                # Build map of sprint points and results
                for _, row in sprint_df.iterrows():
                    # Ergast: givenName, familyName, points, positionText
                    first = row['givenName']
                    last = row['familyName']
                    
                    # [FIX] Normalize Key
                    unique_key = f"{normalize_name(last)}_{normalize_name(first)}"
                    
                    pts = float(row['points'])
                    if pts > 0:
                        # [FIX] Use Full Name as key to match 'primary' driver map in history
                        sprint_points_map[f"{first} {last}"] = pts
                        
                    # Capture result text (e.g. "1", "R")
                    # We store it keyed by normalized name to match frontend usage
                    pos_text = str(row['positionText']) 
                    # Normalize 'R' to 'DNF' for consistency if desired, or keep as is.
                    if pos_text == 'R': pos_text = 'DNF'
                    sprint_results_map[unique_key] = pos_text

                        
                # If we have valid sprint points, we need to generate an intermediate step.
                # We need the "Previous Standings" to add these points to.
                # if i == 0 (Round 1), previous points are 0.
                
                previous_standings_list = []
                if history:
                    previous_standings_list = history[-1]['standings']
                
                # We need a comprehensive list of drivers. 
                # The best proxy for "current grid" is the standings_df we just fetched for the Main Race.
                # However, we need to subtract the Race points to get "Pre-Race" points?
                # A safer bet: Take the 'previous_standings_list'. 
                # Clone it. Update points for those in 'sprint_points_map'.
                # Add any new drivers appearing in sprint but not in previous standings (rare).
                
                # Let's clone the previous state
                sprint_standings_state = copy.deepcopy(previous_standings_list)
                
                # Map for easy update
                sprint_driver_map = {d['name']: d for d in sprint_standings_state}
                
                # Update with sprint points
                for drv_name, pts in sprint_points_map.items():
                    if drv_name in sprint_driver_map:
                        sprint_driver_map[drv_name]['points'] += pts
                    else:
                        # Driver not in previous standings (e.g. first race or substitute)
                        # We should create an entry. 
                        # We might lack color/first name here if we rely solely on previous.
                        # For now, let's try to grab metadata from the sprint_df if possible, 
                        # or just defer to the robust logic below.
                        pass 

                # Re-convert to list and Sort
                sprint_standings_list = list(sprint_driver_map.values())
                sprint_standings_list.sort(key=lambda x: x['points'], reverse=True)
                
                # Re-assign ranks
                # [NEW] Sprint Logic: Sort by (Points Desc, Previous Rank Asc)
                # This preserves the countback from the previous round for those with Equal Sprint Points.
                
                # Update sort: Points (desc), then Old Rank (asc, handled by d['rank'] from prev step)
                # Note: d['rank'] might be modified in prev step, so it is valid.
                sprint_standings_list.sort(key=lambda x: (float(x['points']) * -1, x.get('rank', 999)))
                
                s_current_assign = 0
                s_prev_points = -1.0
                s_prev_old_rank = -1
                
                for idx, d in enumerate(sprint_standings_list, 1):
                    pts = float(d['points'])
                    old_rank = d.get('rank', 999) # fallback
                    
                    # Logic: If Points match AND Old Rank matches (rare, but possible if tied correctly before)
                    # Then Tie.
                    # Else: Next Rank.
                    
                    if pts == s_prev_points and old_rank == s_prev_old_rank:
                        # Tie
                        d['rank'] = s_current_assign
                    else:
                        # Taking the next available slot?
                        # Since we sorted by countback, we usually just want to enumerate 1, 2, 3...
                        # so different old_rank implies different new_rank.
                        s_current_assign = idx
                        d['rank'] = s_current_assign
                        
                    s_prev_points = pts
                    s_prev_old_rank = old_rank
                    
                # Format Date
                sprint_date = str(event['EventDate'])
                try:
                    s_dt = pd.to_datetime(sprint_date)
                    s_date_str = s_dt.strftime("%d %b")
                except:
                    s_date_str = str(sprint_date)

                # Create the Step
                if sprint_points_map:
                     sprint_step_data = {
                        'round': int(round_num),
                        'eventName': event['EventName'],
                        'session': 'Sprint',
                        'date': s_date_str, 
                        'location': event['Location'],
                        'standings': sprint_standings_list,
                        'raceResults': sprint_results_map
                    }

        except Exception as e:
            # Sprint fetch failed or clean - ignore
            # print(f"  Debug: Check sprint failed: {e}")
            pass

        # 2. Fetch Race Session to get Team Colors (not in Ergast) AND Race Results
        # We only need the 'Race' session for this metadata.
        # We can try to be lightweight.
        
        color_map = {} # LastName -> {Color, TeamName}
        race_results_map = {} # LastName -> Result String
        
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
                       lname = str(driver['LastName'])
                       fname = str(driver['FirstName'])
                       # [FIX] Use unique key to prevent collisions (e.g. schumacher_michael)
                       unique_key = f"{normalize_name(lname)}_{normalize_name(fname)}"
                       
                       # Colors
                       raw_color = driver.get('TeamColor', '')
                       color = f"#{raw_color}" if raw_color else None
                       team = driver.get('TeamName', 'Unknown')
                       color_map[unique_key] = {'color': color, 'team': team}
                       
                       # Results
                       # Position: Float (1.0). ClassifiedPosition: '1', 'R'. Status: 'Finished'.
                       cls_pos = str(driver['ClassifiedPosition'])
                       status = str(driver['Status'])
                       
                       # Determine display string
                       if cls_pos.isdigit():
                           res_str = cls_pos
                       else:
                           # If not classified (R, D, N), use 'DNF' usually or the code
                           # 'R' = Retired, 'D' = Disqualified, 'N' = Not Classified, 'W' = Withdrawn
                           if cls_pos in ['R', 'W', 'N']:
                               res_str = 'DNF'
                           elif cls_pos == 'D':
                               res_str = 'DSQ'
                           else:
                               res_str = cls_pos # Fallback e.g. 'NC'
                        
                       if year == 1997 and lname.lower() == 'schumacher' and fname.lower() == 'michael' and int(round_num) == 17:
                           res_str = 'DSQ'

                       race_results_map[unique_key] = res_str
                       
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
                    print(f"  Warning: Could not fetch session data for colors/results ({e})")
                    break
                    
        if color_retries >= max_color_retries:
             print("  Warning: Skipped colors/results for this round due to rate limits.")

        # 3. Build Standings List
        current_standings = []
        
        # 3. Build Standings List
        current_standings = []
        
        # [NEW] Race Logic: Gap Squash
        # We rely on 'standings_df' being sorted by rank (1, 2, 3... 22) as provided by Ergast.
        # We look at the 'position' column.
        # 1. Trust 'position' for ordering.
        # 2. If 'position' jumps (e.g. 14 -> 22), squash it to (14 -> 15).
        # 3. If 'position' is same (22, 22), keep same assigned rank (15, 15).
        
        r_assigned_rank = 0
        r_prev_api_rank = -999
        r_prev_points = -1.0
        
        # [FIX] Sort by Points first to ignore API Rank bias (e.g. 1997 Schumacher DSQ)
        # We want to calculate rank based on points ourselves primarily.
        standings_df = standings_df.sort_values(by=['points', 'wins'], ascending=[False, False])
        
        visual_rank_counter = 1
        bottom_rank = len(standings_df) # [FIX] Dynamic bottom rank (e.g. 28)

        for idx, row in enumerate(standings_df.iterrows(), 1):
             _, row_data = row
             points = float(row_data['points'])
             
             # Parse API Rank (for reference only)
             try:
                 api_rank = int(float(row_data['position']))
             except (ValueError, TypeError):
                 api_rank = 9999
             
             # Ergast fields: givenName, familyName
             first = row_data['givenName']
             last = row_data['familyName']
             
             # Default: Assign next visual rank
             rank_to_assign = visual_rank_counter

             is_1997_dsq = False
             if year == 1997 and last == 'Schumacher' and first == 'Michael' and int(round_num) == 17:
                 is_1997_dsq = True
                 rank_to_assign = bottom_rank # Force to dynamic bottom (DSQ)
             
             # If NOT DSQ, consume the rank slot
             if not is_1997_dsq:
                 visual_rank_counter += 1

             r_assigned_rank = rank_to_assign
             r_prev_api_rank = api_rank

             teams = row_data.get('constructorNames', [])
             team_name = teams[-1] if len(teams) > 0 else "Unknown"
             
             # [FIX] Use robust normalized key
             lname_key = normalize_name(last)
             fname_key = normalize_name(first)
             unique_lookup = f"{lname_key}_{fname_key}"
             
             color = None
             if unique_lookup in color_map:
                 color = color_map[unique_lookup]['color']
             
             rank_display = str(rank_to_assign)
             if is_1997_dsq:
                 rank_display = "DSQ"
             
             current_standings.append({
                 'name': f"{first} {last}", # Full Name
                 'firstName': first,
                 'lookupKey': unique_lookup, # Pass key to frontend
                 'points': points,
                 'team': team_name,
                 'color': color,
                 'rank': rank_to_assign,
                 'rankDisplay': rank_display
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
        # 1. Sprint Step (if available)
        if sprint_step_data:
            # Propagate colors from the main race lookup if missed
            for d in sprint_step_data['standings']:
                # [FIX] Use lookupKey if available (it might be if copied from prev)
                # But if new driver in sprint?
                # We need to construct it if missing.
                if 'lookupKey' not in d:
                     # Attempt to construct from name if possible (risky) or skip
                     # Actually, sprint_data copies from previous, so valid drivers have it.
                     pass 
                
                l_key = d.get('lookupKey')
                if not d.get('color') and l_key and l_key in color_map:
                    d['color'] = color_map[l_key]['color']
            
            history.append(sprint_step_data)
            print(f"  Recorded SPRINT standings for Round {round_num}")

        # 2. Race Step
        step_data = {
            'round': int(round_num),
            'eventName': event['EventName'],
            'session': 'Race', # Implies "Post-Race Standings"
            'date': date_str,
            'location': location,
            'standings': current_standings,
            'raceResults': race_results_map
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
