import fastf1
import pandas as pd
import os
import json

# Enable cache
if not os.path.exists('f1_cache'):
    os.makedirs('f1_cache')
fastf1.Cache.enable_cache('f1_cache')

def prepare_data():
    print("Fetching 2025 Season Schedule...")
    schedule = fastf1.get_event_schedule(2025)
    
    # We will build a list of "steps". Each step is a Race or a Sprint.
    # We need to maintain the cumulative points state.
    
    cumulative_points = {} # Dict[DriverName] -> Points
    history = [] # List of steps
    
    # Get all drivers first? No, we can discover them as we go.
    
    for i, event in schedule.iterrows():
        round_num = event['RoundNumber']
        print(f"Processing Round {round_num}: {event['EventName']}")
        
        # Check for Sprint
        # 2025 formats like 'sprint_qualifying' indicate a sprint weekend.
        has_sprint = (event['EventFormat'] in ['sprint', 'sprint_qualifying', 'sprint_shootout'])
        
        # We need to handle chronological order. Sprints usually happen before Races.
        
        sessions_to_process = []
        if has_sprint:
            sessions_to_process.append(('Sprint', 'S'))
        sessions_to_process.append(('Race', 'R'))
        
        for session_name, session_code in sessions_to_process:
            try:
                session = fastf1.get_session(2025, round_num, session_code)
                session.load(telemetry=False, weather=False, messages=False)
                
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
                    
                    # Store team/full name mapping if needed, but simple update is fine
                    if name not in cumulative_points:
                        cumulative_points[name] = {'points': 0, 'team': team, 'firstName': driver['FirstName']}
                        
                    cumulative_points[name]['points'] += points
                    # Update team if it changed (unlikely mid-season but possible)
                    cumulative_points[name]['team'] = team
                
                # Create sorted standings list
                current_standings = []
                for name, data in cumulative_points.items():
                    current_standings.append({
                        'name': name,
                        'firstName': data['firstName'],
                        'points': data['points'],
                        'team': data['team']
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
                print(f"  Error processing {session_name}: {e}")

    # Save to JSON
    with open('standings_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    print("Saved standings_history.json")

if __name__ == "__main__":
    prepare_data()
