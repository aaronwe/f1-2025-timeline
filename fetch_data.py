import fastf1
import pandas as pd
import os

# Enable cache
if not os.path.exists('f1_cache'):
    os.makedirs('f1_cache')
fastf1.Cache.enable_cache('f1_cache')

def fetch_2025_data():
    print("Fetching 2025 Season Schedule...")
    schedule = fastf1.get_event_schedule(2025)
    
    # Filter for completed events (or all/up to current date since we are in late 2025)
    # We'll just try to fetch all that have happened.
    # The 'EventDate' can be used to filter future events if needed, 
    # but get_event_schedule usually returns the full calendar.
    # We will iterate and try to load results.
    
    all_results = []
    
    # Get races and sprints
    for i, event in schedule.iterrows():
        # Check if event has happened (basic check could be date, or just try fetching)
        # fastf1 usually handles this gracefully.
        print(f"Processing Round {event['RoundNumber']}: {event['EventName']}")
        
        # Determine session types to fetch
        # We need points-paying sessions: 'Race' is standard. 'Sprint' is possible.
        
        # 1. Main Race
        try:
            race = fastf1.get_session(2025, event['RoundNumber'], 'R')
            race.load(telemetry=False, weather=False, messages=False) # lighter load
            
            if 'Points' in race.results.columns:
                results = race.results[['Abbreviation', 'DriverId', 'TeamName', 'Points']].copy()
                results['Round'] = event['RoundNumber']
                results['Session'] = 'Race'
                all_results.append(results)
            else:
                print(f"  No points data for Round {event['RoundNumber']} Race")
        except Exception as e:
            print(f"  Could not load Race for Round {event['RoundNumber']}: {e}")
            continue

        # 2. Sprint (if applicable)
        # Sprints are usually explicitly defined in the schedule, but let's check for 'Sprint' session type availability
        # The schedule object has format columns like 'Session1', 'Session2', etc. or explicitly 'Sprint'.
        # However, fastf1.get_session also accepts 'S' for Sprint.
        if event['EventFormat'] == 'sprint': # FastF1 indicates format
             try:
                sprint = fastf1.get_session(2025, event['RoundNumber'], 'S')
                sprint.load(telemetry=False, weather=False, messages=False)
                
                if 'Points' in sprint.results.columns:
                    s_results = sprint.results[['Abbreviation', 'DriverId', 'TeamName', 'Points']].copy()
                    s_results['Round'] = event['RoundNumber']
                    s_results['Session'] = 'Sprint'
                    all_results.append(s_results)
                    print(f"  Loaded Sprint results")
             except Exception as e:
                print(f"  Could not load Sprint for Round {event['RoundNumber']}: {e}")

    if not all_results:
        print("No results found.")
        return

    # Combine all results
    df_all = pd.concat(all_results)
    
    # Save raw data
    df_all.to_csv('f1_2025_raw_points.csv', index=False)
    print("Saved raw points data to f1_2025_raw_points.csv")

    # Aggregate cumulative points
    # We want a DataFrame: Index=Round, Columns=Driver, Values=Cumulative Points
    
    # First, sum points per driver per round (Race + Sprint)
    df_round_total = df_all.groupby(['Round', 'Abbreviation'])['Points'].sum().reset_index()
    
    # Pivot
    df_pivot = df_round_total.pivot(index='Round', columns='Abbreviation', values='Points').fillna(0)
    
    # Cumulative Sum
    df_cumulative = df_pivot.cumsum()
    
    df_cumulative.to_csv('f1_2025_cumulative_standings.csv')
    print("Saved cumulative standings to f1_2025_cumulative_standings.csv")
    print(df_cumulative.tail())

if __name__ == "__main__":
    fetch_2025_data()
