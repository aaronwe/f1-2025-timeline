import json
import glob

def check_coverage():
    # Load fallbacks
    with open('fallback_teams.json', 'r') as f:
        fallbacks = json.load(f)
    print(f"Loaded {len(fallbacks)} fallback colors.")

    # Scan data
    files = glob.glob('data/standings_history_*.json')
    teams_in_data = set()
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                history = json.load(f)
            for step in history:
                for driver in step.get('standings', []):
                    team = driver.get('team')
                    if team:
                        teams_in_data.add(team)
        except:
            pass
            
    # Check coverage
    missing = []
    for team in teams_in_data:
        if team not in fallbacks:
            missing.append(team)
            
    print(f"Teams in data: {len(teams_in_data)}")
    print(f"Teams missing from fallback: {len(missing)}")
    
    if missing:
        print("MISSING:", missing)
    else:
        print("SUCCESS: All teams are covered by fallback_teams.json")

if __name__ == "__main__":
    check_coverage()
