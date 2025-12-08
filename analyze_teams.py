import fastf1
import pandas as pd
import os

# Enable cache
if not os.path.exists('f1_cache'):
    os.makedirs('f1_cache')
fastf1.Cache.enable_cache('f1_cache')

def audit_teams():
    all_teams = set()
    
    # 2025 might allow future querying, but let's cap at current date context or 2025
    # FastF1 usually supports back to 2018 well, and partial before. 
    # Actually FastF1 supports data back to 2018 for telemetry, but results/schedule go back to 1950.
    
    start_year = 1995
    end_year = 2025
    
    print(f"Auditing teams from {start_year} to {end_year}...")

    for year in range(start_year, end_year + 1):
        try:
            schedule = fastf1.get_event_schedule(year)
            if schedule.empty:
                print(f"{year}: No schedule found.")
                continue
            
            # Get the last official race round to see who finished the season
            # Filtering for 'Race' events only
            races = schedule[schedule['EventFormat'] == 'conventional'] # Heuristic
            # Better: just use get_session(year, round)
            
            # Let's just grab the last event that looks like a race
            count = 0
            # Try the last round first
            last_round = schedule.iloc[-1]['RoundNumber']
            
            try:
                session = fastf1.get_session(year, last_round, 'R')
                session.load(telemetry=False, weather=False, messages=False)
                
                if hasattr(session, 'results') and not session.results.empty:
                    teams = session.results['TeamName'].dropna().unique()
                    new_teams = [t for t in teams if t not in all_teams]
                    if new_teams:
                        pass # print(f"  New in {year}: {new_teams}")
                    
                    all_teams.update(teams)
                    print(f"{year}: Loaded {len(teams)} teams.")
                else:
                    print(f"{year}: No results for Round {last_round}")
            except Exception as e:
                print(f"{year}: Error loading Round {last_round}: {e}")

        except Exception as e:
            print(f"Error processing {year}: {e}")

    print("\n" + "="*30)
    print("UNIQUE TEAM NAMES (1995-2025)")
    print("="*30)
    
    sorted_teams = sorted(list(all_teams))
    for team in sorted_teams:
        print(team)

if __name__ == "__main__":
    audit_teams()
