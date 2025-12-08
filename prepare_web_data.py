import fastf1
import pandas as pd
import os
import json
import argparse
import sys
import time

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

    # We will build a list of "steps". Each step is a Race or a Sprint.
    # We need to maintain the cumulative points state.
    
    cumulative_points = {} # Dict[DriverName] -> Points
    history = [] # List of steps
    
    # Get all drivers first? No, we can discover them as we go.
    
    data_downloaded = False

    for i, event in schedule.iterrows():
        round_num = event['RoundNumber']
        print(f"Processing Round {round_num}: {event['EventName']}")
        
        # Check for Sprint
        # 2025 formats like 'sprint_qualifying' indicate a sprint weekend.
        # Older years might just be 'sprint'. This list covers recent variations.
        has_sprint = (event['EventFormat'] in ['sprint', 'sprint_qualifying', 'sprint_shootout'])
        
        # We need to handle chronological order. Sprints usually happen before Races.
        
        sessions_to_process = []
        if has_sprint:
            sessions_to_process.append(('Sprint', 'S'))
        sessions_to_process.append(('Race', 'R'))
        
        for session_name, session_code in sessions_to_process:
            try:
                session = fastf1.get_session(year, round_num, session_code)
                session.load(telemetry=False, weather=False, messages=False)
                data_downloaded = True
                
                if 'Points' not in session.results.columns:
                    print(f"  No points for {session_name}")
                    continue
                
                # Update cumulative points
                # We need columns: FamilyName, TeamName, Points
                # session.results index is usually driver number or position?
                # Actually, iterate through results
                
                # Create a snapshot of standings *after* this session
                
                results_df = session.results.copy()
                
                if results_df.empty:
                     print(f"  Empty results for {session_name}")
                     continue

                # Points awarded in this session - double check if anyone got points
                total_session_points = results_df['Points'].sum()
                if total_session_points == 0:
                     print(f"  No points awarded in {session_name} yet")
                     continue

                for _, driver in results_df.iterrows():
                    name = driver['LastName'] # Use LastName as verified
                    points = driver['Points']
                    team = driver['TeamName']
                    
                    # Extract TeamColor. FastF1 gives hex codes without '#', or empty strings.
                    # We'll prepend '#' if it's missing and valid.
                    raw_color = driver.get('TeamColor', '')
                    color = f"#{raw_color}" if raw_color else None

                    # Store team/full name/color mapping if needed
                    # We store the LATEST known color for the driver's team
                    if name not in cumulative_points:
                        cumulative_points[name] = {
                            'points': 0, 
                            'team': team, 
                            'firstName': driver['FirstName'],
                            'color': color 
                        }
                    
                    cumulative_points[name]['points'] += points
                    # Update team and color if it changed (unlikely mid-season but possible)
                    cumulative_points[name]['team'] = team
                    if color:
                        cumulative_points[name]['color'] = color
                
                # Create sorted standings list
                current_standings = []
                for name, data in cumulative_points.items():
                    current_standings.append({
                        'name': name,
                        'firstName': data['firstName'],
                        'points': data['points'],
                        'team': data['team'],
                        'color': data.get('color', None) # Default to None so animate script handles fallback
                    })
                
                # Sort by points descending
                current_standings.sort(key=lambda x: x['points'], reverse=True)
                
                # Add Rank
                for rank, driver in enumerate(current_standings, 1):
                    driver['rank'] = rank
                
                # Extract metadata
                # Format date: 14 Mar 2025 -> 14 Mar
                event_date = str(event['EventDate'])
                try:
                    # Assuming timestamp string or object
                    dt = pd.to_datetime(event_date)
                    date_str = dt.strftime("%d %b")
                except:
                    date_str = str(event_date)

                location = event['Location']

                # Append to history
                step_data = {
                    'round': int(round_num),
                    'eventName': event['EventName'],
                    'session': session_name, # "Sprint" or "Race"
                    'date': date_str,
                    'location': location,
                    'standings': current_standings
                }
                history.append(step_data)
                print(f"  Recorded {session_name} stats")
                
            except Exception as e:
                msg = str(e).lower()
                if "429" in msg or "rate limit" in msg:
                    raise RateLimitExceededError(f"Rate limit hit during {session_name}: {e}")
                print(f"  Error processing {session_name}: {e}")
            
            # Sleep briefly between sessions
            time.sleep(1)

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
